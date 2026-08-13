"""支持 `python -m paper_harness` 与 `python D:\\aicoding\\Lib\\paper_harness\\__main__.py` 两种入口。"""

import sys
from pathlib import Path

if __package__:
    from .cli import main
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from paper_harness.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
