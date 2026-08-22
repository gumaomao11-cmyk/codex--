# -*- coding: utf-8 -*-
"""
调仓执行规划器：分批 + 限价 + 避开局部高点。
用法:
  python plan_rebalance.py                 # 读 current_holdings_*.csv, 打印分批限价计划
  python plan_rebalance.py --csv <path>    # 指定持仓清单
  python plan_rebalance.py --tranches 3    # 分几批
  python plan_rebalance.py --buffer 0.02   # 限价低于市价的缓冲 (2%)
输出:
  backtest_output/rebalance_plan_YYYYMMDD.csv
关键设计:
  - 不再一次性市价单买在信号价，改为分批 + 限价
  - 对已经冲上近60日高点的标的，提示"等待回踩"，避免追高
"""
import os, argparse
from datetime import date, timedelta
from pathlib import Path
import pandas as pd, numpy as np

try:
    from _paths import OUT
except Exception:
    OUT = Path(__file__).resolve().parent / "backtest_output"
    OUT.mkdir(parents=True, exist_ok=True)

DATA = Path(os.environ.get("STOCK_DATA_DIR") or r"F:\even-codex\us-stock-data")

def load_prices():
    for cand in [Path(os.environ.get("STOCK_DATA_DIR") or "")/"prices.csv",
                 DATA/"prices.csv",
                 Path(__file__).resolve().parent/"data"/"prices.csv"]:
        if cand.exists():
            p = pd.read_csv(cand, index_col=0, parse_dates=True).apply(pd.to_numeric, errors="coerce")
            return p.sort_index()
    raise FileNotFoundError("找不到 prices.csv")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=None)
    ap.add_argument("--tranches", type=int, default=3)
    ap.add_argument("--buffer", type=float, default=0.02)
    ap.add_argument("--high-win", type=int, default=60)
    ap.add_argument("--chase-th", type=float, default=0.97)
    ap.add_argument("--budget", type=float, default=20000.0)
    a = ap.parse_args()

    holdings = Path(a.csv) if a.csv else next(OUT.glob("current_holdings_*.csv"))
    df = pd.read_csv(holdings)
    if "ticker" not in df.columns:
        raise SystemExit("CSV 缺 ticker 列")
    tickers = df["ticker"].astype(str).tolist()
    per_name = round(a.budget / len(tickers), 2)
    per_tranche = round(per_name / a.tranches, 2)

    p = load_prices()
    close = p.iloc[-1]
    today = date.today()
    print("="*78)
    print(f"分批限价调仓计划   生成:{today}   目标:{len(tickers)}只 x ${per_name:,.2f} = ${per_name*len(tickers):,.0f}")
    print(f"分 {a.tranches} 批 x 每批 ${per_tranche:,.2f}/只 | 限价缓冲 {a.buffer*100:.0f}% | 60日高点阈值 {a.chase_th*100:.0f}%")
    print("="*78)
    print(f"{'代码':<6}{'现价':>9}{'60日高':>9}{'距高点':>8}  {'提示':<16} {'Tranche单价':>10}")
    plan = []
    for sym in tickers:
        px = float(close[sym]) if sym in close.index and pd.notna(close[sym]) else np.nan
        if pd.isna(px):
            print(f"{sym:<6}{'--':>9}  数据缺失,跳过")
            continue
        hi = float(p[sym].tail(a.high_win).max()) if sym in p.columns else px
        dist_hi = px / hi
        chase = "接近高点!等回踩" if dist_hi >= a.chase_th else ""
        limit = None
        for tr in range(1, a.tranches+1):
            limit = round(px * (1 - a.buffer*tr), 2)
            if chase and tr > 1:
                limit = min(limit, round(hi*0.97, 2))
            plan.append((sym, tr, (today + timedelta(days=tr)).isoformat(), limit))
        print(f"{sym:<6}{px:>9.2f}{hi:>9.2f}{dist_hi*100:>7.1f}%  {chase:<16} {limit:>10.2f}")
    print("-"*78)
    print("说明: 每个交易日挂一笔限价单; 当日不成交就撤单并于次日重挂; 接近60日高点的标的, 前批等回踩再买。")

    out_csv = OUT / f"rebalance_plan_{today:%Y%m%d}.csv"
    pd.DataFrame(plan, columns=["ticker","tranche","date","limit_price"]).to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"\n计划已保存: {out_csv}")

if __name__ == "__main__":
    main()