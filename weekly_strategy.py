# -*- coding: utf-8 -*-
"""周频动量策略（影子，和月频同时跑）
- 信号：6个月动量、跳过最近1个月（日线近似，约147个交易日回看）
- 重平衡：每周最后一个交易日打分，次交易周建仓，top10 等权
- 输出：当前周频 top10 持仓清单 + 周频回测指标
"""
import os
from pathlib import Path
import numpy as np, pandas as pd

DATA = Path(os.environ.get("STOCK_DATA_DIR") or r"F:\even-codex\us-stock-data")
OUT = Path(__file__).resolve().parent / "backtest_output"
DAYS = 252; START = 20000.0; TOP = 10; CAPITAL = 20000.0

px = pd.read_csv(DATA/"prices.csv", index_col=0, parse_dates=True).sort_index().apply(pd.to_numeric, errors="coerce")
px = px.loc[:, px.count() >= 2400]
idx = px.index; cols = list(px.columns); idpos = {d:i for i,d in enumerate(idx)}
dr = px.pct_change().fillna(0.0)

def mom_score(d):  # 日线近似 6m-skip1
    if d - 147 < 0: return None
    a = px.iloc[d-21]; b = px.iloc[d-147]
    return (a/b - 1.0).replace([np.inf, -np.inf], np.nan)

def weekly_last_days():
    s = pd.Series(idx, index=idx.to_period("W"))
    last = s.groupby(level=0).last()
    return [int(idpos[d]) for d in last.tolist() if d in idpos]

# ---------- 当前周频持仓 ----------
wk_days = [d for d in weekly_last_days() if d > 147]
sig_i = max(wk_days)
sig_date = idx[sig_i]
sc = mom_score(sig_i)
ta = list(sc.sort_values(ascending=False).index[:TOP])
rows = []
for rk, t in enumerate(ta, 1):
    price = float(px.iloc[-1][t])
    alloc = CAPITAL / TOP
    rows.append(dict(rank=rk, ticker=t, signal_date=str(pd.Timestamp(sig_date).date()),
                     momentum=float(sc[t]), weight=1.0/TOP, price=price,
                     alloc_usd=alloc, shares=alloc/price))
hold = pd.DataFrame(rows)
hold_csv = OUT / "current_holdings_6m_skip1_top10_weekly.csv"
hold.to_csv(hold_csv, index=False, encoding="utf-8-sig")
print("="*80)
print(f"周频动量策略 top{TOP}  信号={pd.Timestamp(sig_date).date()}  数据截止={idx[-1].date()}")
print(hold[["rank","ticker","momentum","price","alloc_usd","shares"]].round(4).to_string(index=False))
print("saved:", hold_csv)

# ---------- 周频回测指标 ----------
def backtest_weekly(top=TOP, cost_bps=10, vol_target=None):
    rb = weekly_last_days()
    rb = [d for d in rb if d > 147 and d+1 < len(idx)]
    prev_w = pd.Series(0.0, index=cols); ret = pd.Series(0.0, index=idx); cost_line = pd.Series(0.0, index=idx)
    for k, rdi in enumerate(rb):
        sc = mom_score(rdi)
        if sc is None or sc.dropna().empty: continue
        ta2 = list(sc.sort_values(ascending=False).index[:top]); w = 1.0/len(ta2)
        new_w = pd.Series(0.0, index=cols); new_w[ta2] = w
        to = (new_w - prev_w).abs().sum()/2.0
        hold_start = rdi + 1
        seg_end = rb[k+1] if k+1 < len(rb) else len(idx)-1
        if seg_end <= hold_start: seg_end = hold_start + 1
        cost_line.iloc[hold_start] += to * cost_bps / 10000.0
        li = [cols.index(c) for c in ta2 if c in cols]
        if li:
            ret.iloc[hold_start:seg_end+1] += (dr.iloc[hold_start:seg_end+1, li] * w).sum(axis=1)
        prev_w = new_w.copy()
    if vol_target:
        scale = pd.Series(1.0, index=ret.index)
        for k, rdi in enumerate(rb):
            hs = rdi + 1
            if hs >= len(idx): continue
            look = ret.loc[:idx[hs]].iloc[-(61):-1].dropna()
            if len(look) >= 21 and look.std(ddof=1) > 0:
                sval = min(1.0, vol_target/(look.std(ddof=1)*np.sqrt(DAYS)))
                se = rb[k+1] if k+1 < len(rb) else len(idx)-1
                scale.iloc[hs:se+1] = sval
        ret = ret.mul(scale)
    return (ret - cost_line).clip(lower=-0.5)

def metrics(ret):
    nav = (1+ret).cumprod()*START
    ann = (nav.iloc[-1]/START)**(DAYS/len(nav))-1
    vol = ret.std(ddof=1)*np.sqrt(DAYS)
    sh = ann/vol if vol>0 else np.nan
    mdd = (nav/nav.cummax()-1).min()
    return dict(ann=ann, vol=vol, sharpe=sh, mdd=float(mdd), final=float(nav.iloc[-1]))

r = backtest_weekly(); f = metrics(r)
r25 = backtest_weekly(vol_target=0.25); f25 = metrics(r25)
oos = idx >= pd.Timestamp("2022-01-01"); o = metrics(r[oos]); o25 = metrics(r25[oos])
def line(name, mm, oo):
    return dict(策略=name, full_sh=round(mm["sharpe"],3), full_ann=round(mm["ann"],4), full_mdd=round(mm["mdd"],4), full_end=round(mm["final"],0),
                oos_sh=round(oo["sharpe"],3), oos_ann=round(oo["ann"],4), oos_mdd=round(oo["mdd"],4), oos_end=round(oo["final"],0))
mdf = pd.DataFrame([line("周频 6m-skip1 top10 (base)", f, o),
                    line("周频 6m-skip1 top10 + vol25（推荐）", f25, o25)])
mcsv = OUT / "weekly_backtest_metrics.csv"
mdf.to_csv(mcsv, index=False, encoding="utf-8-sig")
print("\n周频回测指标:")
print(mdf.to_string(index=False))
print("saved:", mcsv)
