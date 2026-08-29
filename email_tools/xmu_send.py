# -*- coding: utf-8 -*-
"""Shared XMU SMTP send helper. Always applies default_cc from global config."""
from __future__ import annotations

import json
import smtplib
import ssl
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from pathlib import Path
from typing import Iterable, Sequence

CFG_PATH = Path(r"D:\aicoding\mylib\email_tools\xmu_mail_global_config.json")


def load_cfg(path: Path = CFG_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: str | Iterable[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [x for x in value if x and str(x).strip()]


def send_utf8_mail(
    to: str | Sequence[str],
    subject: str,
    body: str,
    *,
    cc: str | Sequence[str] | None = None,
    apply_default_cc: bool = True,
    from_display: str = "厦大邮箱",
    cfg: dict | None = None,
) -> str:
    """Send plain-text UTF-8 mail via XMU SMTP; merges cfg default_cc unless disabled."""
    cfg = cfg or load_cfg()
    from_addr = cfg["default_from"]
    password = cfg["smtp"]["password"]
    host = cfg["smtp"]["host"]
    port = int(cfg["smtp"]["port"])

    to_list = _as_list(to)
    cc_list = _as_list(cc)
    if apply_default_cc:
        for addr in _as_list(cfg.get("default_cc")):
            if addr not in to_list and addr not in cc_list:
                cc_list.append(addr)

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((str(Header(from_display, "utf-8")), from_addr))
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Subject"] = Header(subject, "utf-8")
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(body, "plain", "utf-8"))

    recipients = list(dict.fromkeys(to_list + cc_list))
    context = ssl.create_default_context()
    print(f"Connecting {host}:{port}")
    print(f"To: {to_list} | Cc: {cc_list}")
    with smtplib.SMTP_SSL(host, port, context=context, timeout=90) as server:
        server.login(from_addr, password)
        server.sendmail(from_addr, recipients, msg.as_string())
    return "SENT_OK via SMTP_SSL"
