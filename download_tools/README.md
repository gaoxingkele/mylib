# Global Download Tools

跨项目复用的下载工具库。核心原则：**优先使用 aria2c**，不可用或失败时回退到 `curl`、`wget` 或 Python `urllib`。

## 安装 / 引用

本库无需安装，可通过 Python 路径直接导入。

### 方式 1：临时将 `D:\aicoding\mylib` 加入 `PYTHONPATH`

```powershell
$env:PYTHONPATH = "D:\aicoding\mylib;$env:PYTHONPATH"
python -c "from download_tools import download; download('https://example.com/file.zip', 'data/file.zip')"
```

### 方式 2：在项目中把 `D:\aicoding\mylib` 加入 `sys.path`

```python
import sys
from pathlib import Path
sys.path.insert(0, r"D:\aicoding\mylib")

from download_tools import download

download(
    "https://example.com/file.zip",
    Path("data/file.zip"),
    proxy="http://127.0.0.1:17890",
)
```

### 方式 3：命令行直接调用

```powershell
python D:\aicoding\mylib\download_tools\download.py https://example.com/file.zip data/file.zip
```

## API

### `download(url, dest, *, proxy=..., use_aria2=True, fallback=True, **aria2_kwargs)`

- `url`: 远程地址
- `dest`: 本地路径或目录；如果是目录，自动从 URL 推断文件名
- `proxy`: 代理地址，默认 `http://127.0.0.1:17890`；传 `None` 禁用
- `use_aria2`: 是否优先使用 aria2c
- `fallback`: aria2c 失败/不可用时是否回退
- `aria2_kwargs`: 传给 aria2c 的参数，如 `split=32`

返回退出码 `0` 表示成功。

### `download_many(items, **kwargs)`

批量下载：

```python
items = [
    ("https://a.com/1.zip", "out/1.zip"),
    ("https://a.com/2.zip", "out/2.zip"),
]
results = download_many(items, stop_on_error=False)
```

### 单独使用 aria2c 或 fallback

```python
from download_tools import find_aria2, download_with_aria2
from download_tools.fallback import download_with_curl

aria2_path = find_aria2()
```

## aria2c 默认参数

```text
--split=16
--max-connection-per-server=16
--min-split-size=1M
--continue=true
--file-allocation=none
--max-tries=0
--retry-wait=5
--timeout=60
--connect-timeout=30
--auto-file-renaming=false
--allow-overwrite=true
--all-proxy=http://127.0.0.1:17890
```

## 已知 aria2c 路径

如果 `aria2c` 不在 `PATH` 中，会按顺序查找：

1. `C:\Users\10175\AppData\Local\aria2\aria2-1.37.0-win-64bit-build1\aria2c.exe`
2. `C:\Users\10175\AppData\Local\aria2c.exe`
3. `C:\Program Files\Netease\GameViewer\bin\aria2c.exe`
