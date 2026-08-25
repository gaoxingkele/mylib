# XMU Mail Global Config

Config file: `D:\aicoding\Lib\email_tools\xmu_mail_global_config.json`

- From: `iamafan@xmu.edu.cn`
- **Default Cc: `iamafan@126.com`** (always applied by `xmu_send.py`)
- SMTP: `smtp.xmu.edu.cn` (465 SSL)
- IMAP: `imap.xmu.edu.cn`
- POP3: `pop3.xmu.edu.cn`
- Alias: `mail.xmu.edu.cn`
- Encoding: UTF-8

Send helper:

```bash
python -c "from xmu_send import send_utf8_mail; ..."
# or import from D:\aicoding\Lib\email_tools\xmu_send.py
```
