# 操作清单：自动跑 vs 需要手动

## 一、已自动化（不用管）
每天美股收盘后（建议北京时间 05:30 触发）`run_daily_update.bat` 会自动做：
- 增量更新 `F:\even-codex\us-stock-data`（raw/ → prices.csv / summary.csv）
- 增量更新 `F:\even-codex\panda\backtest\prices_2016.csv`（ETF 参照表）
- 日志：`F:\even-codex\lianghua2\logs\daily_update_cron.log` 和 `F:\even-codex\panda\backtest\etf_ref_update.log`

异常自查：
- 看一下日志最后一行；如果连续几天都是 `no new rows returned.` 但你知道当天有交易，去看一眼 NASDAQ 接口或网络。
- 偶尔 `FAIL sym` 是单只票拉取失败，不要紧，脚本会跳过那一只。

## 二、需要手动做的事

### 每天 1 分钟（美股收盘后）
- [ ] 跑 `python paper_tracker.py`，看日报
  - 重点看：`期间最高回撤` / `相对 SPY 的 alpha` / `近 21 日夏普`
  - 文件：`F:\even-codex\lianghua2\backtest_output\paper_log.csv`（自动追加）

### 每周 5 分钟（周末或周一）
- [ ] 跑 `python shadow_compare.py`
  - 看其它候选项（top15/top20/3m/9m/加波动率目标）的同期表现
  - 3 个月结束后用真数据决策时用得着

### 每月末（最后一个美股交易日）
- [ ] `python current_holdings.py` 生成新 top10 清单
- [ ] `python alpaca_buy.py --rebalance --dry-run` 看调仓计划
- [ ] 确认后 `python alpaca_buy.py --rebalance --execute` 实际调仓
- [ ] 周末翻一下这一月 paper_log.csv 的夏普和回撤曲线

### 每季度（每 3 个月）评估一次
- [ ] 跑 `python walkforward_v6.py` 看滚动选参结果是否有变化
- [ ] 跑一次成本敏感度（修改 `correct_metrics.py` 里 cost_bps 参数），确认 10bps 假设仍合理
- [ ] **3 个月满了**：综合 `paper_log.csv` 和 `shadow_compare.py` 写一份 `backtest_output/3m_review.md` 评估报告
  - 实际夏普 vs 回测预期
  - 实际最大回撤 vs 预期
  - 影子策略里有没有更好的
  - 决定：保留 / 切换配置 / 切真钱账户

### 每半年（建议每 6 个月）
- [ ] 重新跑回测，看参数还稳定不（重点看 OOS 段）
- [ ] 看数据池是否需要更新：
  - 有没有新成分股加入（IPO 后进入 S&P500/NDX）
  - 老的成分股被踢出/退市
  - 当前 `count >= 2400` 的过滤可能把新股过早排除，可以考虑加一个“近 1 年新进入指数”的备用池

### 任何时候（异常情况）
- [ ] 看到日报里 `期间最高回撤` 超过 -40% → 考虑提前切到 top20 或加波动率目标
- [ ] 看到 `相对 SPY 的 alpha` 连续 1 个月低于 -5% → 暂停调仓，先看 1-2 周
- [ ] key / 凭据疑似泄露（像之前那次）→ 立即去 Alpaca 控制台 Revoke + 重建
- [ ] 想加新的策略候选 → 复制 `alpaca_buy.py` 改成新配置，作为影子策略先看 1 个月再决定是否启用

### GitHub 同步（你之前说想推 GitHub）
- [ ] 跑完一次 `git add -A && git commit -m "..."`，再 push 到你的远程仓库
- [ ] 每次改了策略或脚本后顺手 commit，方便回滚

## 三、关键文件位置速查
| 文件 | 用途 |
|---|---|
| `F:\even-codex\lianghua2\paper_log.csv` | 模拟盘日报数据 |
| `F:\even-codex\lianghua2\backtest_output\paper_state.json` | paper 起始日 / 起始权益 |
| `F:\even-codex\lianghua2\backtest_output\current_holdings_6m_skip1_top10.csv` | 当前 top10 持仓清单 |
| `F:\even-codex\lianghua2\backtest_output\aggressive_strategy_spec.md` | 激进版策略规格 |
| `F:\even-codex\lianghua2\backtest_output\paper_3month_plan.md` | 3 个月测试操作手册 |
| `F:\even-codex\lianghua2\backtest_output\optimization_report.md` | 优化实验报告 |
| `F:\even-codex\us-stock-data\logs\daily_update.log` | 数据自动更新日志 |
| `F:\even-codex\panda\backtest\etf_ref_update.log` | ETF 参照表更新日志 |

## 四、节奏总览
| 频率 | 做什么 | 耗时 |
|---|---|---|
| 自动（每天） | 数据增量更新 | 1-3 分钟 |
| 每天 | 跑 paper_tracker | 1 分钟 |
| 每周 | 跑 shadow_compare | 1 分钟 |
| 每月末 | 调仓（4 步） | 10-15 分钟 |
| 每季度 | walkforward + 成本敏感度 + 3m 评估 | 1-2 小时 |
| 每半年 | 回测再验证 + 数据池体检 | 半天 |
