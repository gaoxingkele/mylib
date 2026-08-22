# -*- coding: utf-8 -*-
"""incoPat 开放数据平台 API 客户端（测试环境 apitest.incopat.com）

用法:
  python incopat_api.py search   "TI-CN=(变压器 AND 故障诊断) AND PNC=CN" [--rows 10] [--from 0] [--order "PD DESC"] [--fields pn,ti-cn,...]
  python incopat_api.py count    "检索式"            # 无权限时会明确报错
  python incopat_api.py semantic "一段技术方案描述文字" [--rows 10]
  python incopat_api.py claim    CN103399241B        # 权利要求全文
  python incopat_api.py spec     CN103399241B        # 说明书全文
  python incopat_api.py legal    CN103399241B        # 法律状态 2.0
  python incopat_api.py value    CN103399241B        # 合享价值度评分
  python incopat_api.py assign   CN103399241B        # 转让
  python incopat_api.py licence  CN103399241B        # 许可
  python incopat_api.py reexam   CN103399241B        # 复审无效
  python incopat_api.py batch    CN1234A CN5678B --cmd claim   # 批量取多个 pn

凭证优先级: 环境变量 INCOPAT_* > 同目录 credentials.json（已 gitignore，模板见 credentials.example.json）。
token 缓存在本文件同目录 .token_cache.json，有效期 2 小时自动刷新。
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_CRED_FILE = os.path.join(_HERE, "credentials.json")
_cred = {}
if os.path.exists(_CRED_FILE):
    with open(_CRED_FILE, encoding="utf-8") as _f:
        _cred = json.load(_f)

BASE = os.environ.get("INCOPAT_BASE", _cred.get("base", "https://apitest.incopat.com"))
CLIENT_ID = os.environ.get("INCOPAT_CLIENT_ID", _cred.get("client_id", ""))
CLIENT_SECRET = os.environ.get("INCOPAT_CLIENT_SECRET", _cred.get("client_secret", ""))
USERNAME = os.environ.get("INCOPAT_USERNAME", _cred.get("username", ""))
PASSWORD = os.environ.get("INCOPAT_PASSWORD", _cred.get("password", ""))
if not (CLIENT_ID and CLIENT_SECRET and USERNAME and PASSWORD):
    raise SystemExit("缺少 incoPat 凭证：请在 scripts/credentials.json 填写（模板 credentials.example.json），或设 INCOPAT_* 环境变量")

TOKEN_CACHE = os.path.join(_HERE, ".token_cache.json")

# 测试账号实测可用的返回字段（ipc/lgd/status-lite 等无权限）
DEFAULT_FIELDS = "pn,an,ti-cn,ti-en,ab-cn,ap-or,in-or,agc,ad,pd"


def _post(path, params, timeout=60):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {body[:500]}")


def get_token(force=False):
    if not force and os.path.exists(TOKEN_CACHE):
        try:
            with open(TOKEN_CACHE, encoding="utf-8") as f:
                c = json.load(f)
            if c.get("expires_at", 0) > time.time() + 60 and c.get("client_id") == CLIENT_ID:
                return c["access_token"]
        except Exception:
            pass
    resp = _post("/oauth/token", {
        "grant_type": "password", "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET, "username": USERNAME, "password": PASSWORD})
    if "access_token" not in resp:
        raise SystemExit(f"获取 token 失败: {json.dumps(resp, ensure_ascii=False)}")
    with open(TOKEN_CACHE, "w", encoding="utf-8") as f:
        json.dump({"access_token": resp["access_token"], "client_id": CLIENT_ID,
                   "expires_at": time.time() + int(resp.get("expires_in", 7200))}, f)
    return resp["access_token"]


def api(path, params):
    """自动带 token 调接口；token 失效自动重取一次。"""
    params = dict(params)
    params["access_token"] = get_token()
    resp = _post(path, params)
    msg = str(resp.get("message", ""))
    if resp.get("status") is False and ("TOKEN" in msg.upper() or resp.get("code") in (1006, 1007, "1006", "1007")):
        params["access_token"] = get_token(force=True)
        resp = _post(path, params)
    return resp


def pretty(resp):
    print(json.dumps(resp, ensure_ascii=False, indent=2))
    if resp.get("status") is False:
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="incoPat API client")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="检索式检索 (incosearch)")
    s.add_argument("exp", help="incoPat 检索式, 如 TI-CN=(变压器) AND PNC=CN AND PD=[20200101 TO 20261231]")
    s.add_argument("--rows", type=int, default=10, help="返回条数 1-20")
    s.add_argument("--from", dest="frm", type=int, default=0)
    s.add_argument("--order", default="", help="如 'PD DESC' 或 'relevancy DESC'")
    s.add_argument("--fields", default=DEFAULT_FIELDS)

    c = sub.add_parser("count", help="检索式命中总量")
    c.add_argument("exp")

    m = sub.add_parser("semantic", help="语义检索（技术方案文字→相似专利）")
    m.add_argument("text", help="词/语句/段落, 中国专利用中文")
    m.add_argument("--rows", type=int, default=10)

    for name, path_help in [("claim", "权利要求"), ("spec", "说明书"), ("legal", "法律状态"),
                            ("value", "合享价值度"), ("assign", "转让"), ("licence", "许可"),
                            ("reexam", "复审无效")]:
        sp = sub.add_parser(name, help=path_help)
        sp.add_argument("pn", help="公开(公告)号, 如 CN103399241B")

    b = sub.add_parser("batch", help="批量按公开号取数据")
    b.add_argument("pns", nargs="+")
    b.add_argument("--cmd", default="claim", choices=["claim", "spec", "legal", "value", "assign", "licence", "reexam"])

    a = p.parse_args()
    cid = CLIENT_ID
    pn_paths = {"claim": f"/api/search/claim/{cid}", "spec": f"/api/search/spec/{cid}",
                "legal": f"/api/search/lgtxt2/{cid}", "value": f"/api/search/vlstar/{cid}",
                "assign": f"/api/search/assign/{cid}", "licence": f"/api/search/licence/{cid}",
                "reexam": f"/api/search/reetxt/{cid}"}

    if a.cmd == "search":
        params = {"incoExp": a.exp, "rows": a.rows, "from": a.frm, "incoFields": a.fields}
        if a.order:
            params["order"] = a.order
        pretty(api(f"/api/search/incosearch/{cid}", params))
    elif a.cmd == "count":
        pretty(api(f"/api/search/count/{cid}", {"incoExp": a.exp}))
    elif a.cmd == "semantic":
        pretty(api(f"/api/semanticsApi/semanticsSearch/{cid}", {"searchText": a.text, "rows": a.rows}))
    elif a.cmd == "batch":
        out = {}
        for pn in a.pns:
            out[pn] = api(pn_paths[a.cmd], {"pn": pn})
            time.sleep(0.15)  # 限速: 默认每秒最多 10 请求
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        pretty(api(pn_paths[a.cmd], {"pn": a.pn}))


if __name__ == "__main__":
    main()
