# 3个月模拟盘验证 + 中途优化（操作手册）

## 核心原则
- **测试期不要动主配置**（6m skip1 前10只），否则测出来的就不是这个策略了。
- 同时开几个“影子策略”用本地历史数据同步跑，便于事后对比哪种更合适。
- 三个月结束后再决定是否切到别的配置/真钱账户。

## 配套脚本（都在 F:\even-codex\lianghua2）
- `alpaca_buy.py`           下单/调仓（凭据从本地 alpaca.env 读，不要贴到聊天）
- `paper_tracker.py`        拉模拟账户当日数据，写 paper_log.csv，出日报
- `shadow_compare.py`       用本地数据模拟其它候选项，对比实际表现
- `current_holdings.py`     每月末生成新 top10 持仓清单

## 时间表
- **T+0（今天，已完成）**：按 top10 买入 10 只各 2000 美元。
- **每周一 ~ 周五**（收盘后）跑：`python paper_tracker.py`
  - 累计持仓、相对 SPY 的 alpha、回撤、近 21 日夏普会一并打印。
  - 同时把数据写进 `backtest_output/paper_log.csv`。
- **每个月最后一个交易日**（T+30 / T+60）：
  1. `python current_holdings.py` 生成新的 top10 清单；
  2. 跑 `python alpaca_buy.py --rebalance --dry-run` 看调仓计划；
  3. 确认后 `python alpaca_buy.py --rebalance --execute` 实际调仓。
- **T+90（三个月末）**：
  1. 跑 `python paper_tracker.py` 与 `python shadow_compare.py`；
  2. 比较实际 vs 影子的夏普/回撤/alpha；
  3. 用真实数据决定：保留 / 换配置 / 切真钱账户。

## 中途怎么看“效果是否符合预期”
- **每周看一次** paper_tracker 的输出，盯三个数字：
  - `期间最高回撤` —— 不要让它超过 **-40%**（回测样本外最大回撤），突破就考虑切换到 top20 或加波动率目标。
  - `相对 SPY 的 alpha` —— 三个月内 0 以上是底线，3-5% 算正常。
  - `近 21 日夏普` —— 长期均值 1.0-1.5 都算在线。
- **不要因为几天回撤就调参**，动量策略本质上是“赚大波段、挨一段时间小亏”的节奏。

## 中途可以做的“安全优化”（不破坏测试纯度）
1. **加波动率目标**（最不影响测试纯度的附加层）：在 `alpaca_buy.py` 里把 `vol_target=0.25` 加上，把仓位动态调到 25% 目标波动。可以做成一个 `alpaca_buy_vol25.py` 副本跑下一轮。但建议**等 3 个月结束后**用真数据再决定。
2. **把回撤超阈值的“应急降仓”写进规则**（比如 NAV 跌 25% 自动切到 50% 仓位），三个月试完再讨论。
3. **影子策略对照**：不需要额外账户，每天跑 `python shadow_compare.py` 就能看到“假如我当初用 top20/3m/9m 会怎样”，作为 90 天后决策依据。

## 月末调仓的注意事项
- `--rebalance` 模式会**先卖不在目标里的旧持仓，再按当前权益等权买入新目标**。这样不需要手动算清仓位。
- 调仓当周市场波动大时，可以分两天做（先卖后买），避免同一天两笔市价单冲击成本叠加。
- 真实交易里**别忘了周五当天调**——周一开盘价往往比周五收盘差。

## 3 个月结束后的决策清单
- 实际夏普是否在 0.8-1.5 区间？ → 在 → 切真钱
- 实际最大回撤是否超过 45%？ → 超过 → 降级到 top20 或加波动率目标
- 实际 alpha 跑输 SPY 多少？ → 跑输 5% 以上 → 暂停实盘，重做样本外验证
- 影子策略里哪个夏普/回撤更优？ → 列入下一轮配置

## 关键文件路径
- 模拟账户日志：`F:\even-codex\lianghua2\backtest_output\paper_log.csv`
- 模拟账户起点状态：`F:\even-codex\lianghua2\backtest_output\paper_state.json`
- 报告与图表：`F:\even-codex\lianghua2\backtest_output\`
