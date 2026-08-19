# 任务计划程序设置 SOP（自动跑+自动邮件）

## 一次性准备
1. **QQ 邮箱开启 SMTP 并生成授权码**（重要，不要把授权码贴到任何对话/截图）
   - 登录 QQ 邮箱网页版 → 设置 → 账户 → 找到 `IMAP/SMTP/Exchange/CardDAV/CalDAV服务`
   - 开启 `SMTP服务`，点 `生成授权码`，按提示发短信后拿到一串 16 位字符
2. **把授权码写到本地**：`F:\even-codex\lianghua2\mail.env`
   ```ini
   QQ_MAIL_AUTH_CODE=你的16位授权码
   QQ_MAIL_FROM=869357594@qq.com
   QQ_MAIL_TO=869357594@qq.com
   ```
3. **在本地首次跑一次 dry-run** 验证邮件能发：
   ```powershell
   cd F:\even-codex\lianghua2
   python auto_run.py
   ```
   没设 `ALPACA_AUTO_EXECUTE` 时，调仓只会 dry-run，不会真下单。

## 把两个任务挂到任务计划程序
1. 打开“任务计划程序”（开始菜单搜 `Task Scheduler`）
2. 右侧 `Create Task`（**不是** Create Basic Task）→ 填名：
   - Name: `StockData_Update_Daily`
   - User account: 选你自己的 Windows 账户，勾 `Run whether user is logged on or not`
3. **Triggers 标签** → New：
   - Daily，Start: `2026-08-19 05:30:00`
   - 勾 `Enabled`
4. **Actions 标签** → New：
   - Program/script:  `F:\even-codex\lianghua2\run_daily_update.bat`
   - Start in:        `F:\even-codex\lianghua2`
5. **Conditions / Settings** 勾默认即可 → OK，提示输入 Windows 密码确认。

第二个任务同样步骤再建一个：
- Name: `Strategy_AutoRun_Daily`
- Program: `F:\even-codex\lianghua2\run_auto.bat`
- Start in: `F:\even-codex\lianghua2`
- Trigger: 每天 17:00（美股收盘后约 1 小时，Alpaca 数据稳定）

## 自动调仓的开关
- 默认：每月末 dry-run 出调仓计划 + 邮件给你，你点开附件里 `current_holdings_*.csv` 看一眼，然后手动 `python alpaca_buy.py --rebalance --execute`
- 想全自动：把 `ALPACA_AUTO_EXECUTE=1` 写到 `F:\even-codex\lianghua2\mail.env`（同一文件）里即可。改完当天会按新规则跑。

## 出问题怎么排查
- 数据没更新 → 看 `F:\even-codex\lianghua2\logs\daily_update_cron.log` 末尾
- 邮件没收到 → 看 `F:\even-codex\lianghua2\logs\auto_run_cron.log` 和 `auto_paper.log`，里面会有 `[mailer] 发送失败: ...`
- 调仓出错 → 看 `auto_rebalance_dry.log` 或 `auto_rebalance_exec.log`
- 任务没跑 → 在任务计划程序里看 Last Run Result 是否 0x0

## 安全提醒
- **mail.env 已经在 .gitignore 里**，不会被推到 GitHub。
- 如果哪天发现 key 或授权码出现在任何对话/截图里，立刻去 QQ 邮箱 / Alpaca 控制台 Revoke 重建。
