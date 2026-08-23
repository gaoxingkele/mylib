# 全局配置

## 厦大邮箱（邮件发送配置）

当用户要求用"厦大邮箱"发送邮件/文件时，直接调用全局脚本：

```powershell
& D:\Python\Python314\python.exe C:\Users\10175\.claude\scripts\send_xmu_mail.py --to <收件人> --subject "<主题>" --body "<正文>" --attach <附件路径...>
```

- 账号、SMTP 服务器（smtp.xmu.edu.cn:465 SSL）、密码均存于 `C:\Users\10175\.claude\scripts\xmu_mail_config.json`，无需再询问用户。
- 密码可用环境变量 `XMU_MAIL_PASSWORD` 覆盖配置文件中的值。
- 支持多收件人与多附件。

## Python 环境

本机 `python` 命令是 Microsoft Store 的 0 字节占位符，不可用。请使用真实解释器：`D:\Python\Python314\python.exe`（或 `C:\WINDOWS\py.exe -V:3.14`）。
