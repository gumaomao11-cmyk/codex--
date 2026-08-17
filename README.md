# 美股量化 - 非日内动量策略（激进前10只版）

## 目录
- `backtest_momentum.py` / `backtest_momentum_v2.py`：基础回测脚本
- `optimize_*.py`：参数扫描、波动率管理、风险平价等优化实验
- `walkforward_v6.py`：滚动窗口样本外验证
- `correct_metrics.py`：修正口径的 IS/OOS 指标
- `current_holdings.py`：生成最新“前10只”持仓清单
- `yearly_check.py`：逐年稳健性检查
- `backtest_output/`：回测报告、结果表、净值图

## 策略（激进版）
动量：过去 6 个月，跳过最近 1 个月；每月末排序，买入前 10 只等权；每月第一个交易日调仓；满仓不加杠杆；成本按单边 10bps。

关键回测结论（2016-08 ~ 2026-08，2万美元起步）：
- 全期夏普约 1.33，样本外夏普约 1.25
- 样本外最大回撤约 -40%
- 幸存者偏差与未含股息会令实盘打折扣

## 数据说明（重要）
按项目全局规则，所有回测数据统一读取本机 `F:\even-codex\us-stock-data`，**不在 GitHub 上传完整历史数据**。
数据目录结构：
- `master_tickers.csv` / `summary.csv`：标的与行情汇总
- `raw/`：515 只股票原始日线 CSV
- `prices.csv`：收盘价宽表（515 列）
- `ohlcv.pkl`：行情包
- `sec/`、`fundamentals_daily.pkl`：基本面（CODEC 独立大文件）
- `scripts/`：数据下载与构建脚本

统计：整个数据目录约 2.1GB，其中单个 `fundamentals_daily.pkl` 约 1.7GB，超过 GitHub 单文件限制，故不纳入仓库。
支持环境变量 `STOCK_DATA_DIR`，未设置时回退到 `F:\even-codex\us-stock-data`。

大盘/纳指等 ETF 参照：`F:\even-codex\panda\backtest\prices_2016.csv`（SPY/QQQ/IWM/TLT/SPMO/QUAL/USMV/VLUE）。

## 如何运行
```powershell
cd F:\even-codex\lianghua2
python current_holdings.py          # 生成最新前10只持仓
python backtest_momentum_v2.py      # 基础回测
python walkforward_v6.py            # 滚动样本外验证
```

## 说明
- 本仓库只提交代码与报告，不含本地大数据文件。
- 数据需在运行环境存在（见上节路径）。
