"""Download Lucide icons (ISC license) into assets/icons. Browse names at https://lucide.dev/icons

Usage: python tools/fetch_icons.py mic captions volume-2
       python tools/fetch_icons.py --from-main      # every name in ICON_NAMES of src/main.js that is missing
"""
from __future__ import annotations

import re
import sys
import urllib.request

from common import ROOT

VERSION = "0.460.0"
URL = "https://unpkg.com/lucide-static@{v}/icons/{name}.svg"
ICONS = ROOT / "assets" / "icons"


def names_from_main() -> list[str]:
    src = (ROOT / "src" / "main.js").read_text(encoding="utf-8")
    m = re.search(r"ICON_NAMES\s*=\s*\[(.*?)\]", src, re.S)
    return re.findall(r"'([^']+)'", m.group(1)) if m else []


def fetch(name: str) -> bool:
    if not re.fullmatch(r"[a-z0-9-]+", name):
        print(f"skip invalid name: {name}")
        return False
    dest = ICONS / f"{name}.svg"
    if dest.exists():
        return True
    try:
        with urllib.request.urlopen(URL.format(v=VERSION, name=name), timeout=30) as r:
            svg = r.read().decode("utf-8")
    except Exception as err:  # 404 = icon name does not exist in this Lucide version
        print(f"FAIL {name}: {err}")
        return False
    if "<svg" not in svg:
        print(f"FAIL {name}: not an svg")
        return False
    dest.write_text(svg, encoding="utf-8")
    print(f"ok   {name}")
    return True


def main() -> None:
    args = sys.argv[1:]
    names = names_from_main() if args == ["--from-main"] else args
    if not names:
        raise SystemExit(__doc__)
    ICONS.mkdir(parents=True, exist_ok=True)
    failed = [n for n in names if not fetch(n)]
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
