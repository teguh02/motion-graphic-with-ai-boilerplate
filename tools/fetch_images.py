"""Supporting photos from PUBLIC image APIs (no API keys) with automatic provider fallback.

Providers, tried in order until one returns a usable image (a timeout, "too busy", empty result or
broken download moves on to the next provider automatically):
  wikimedia  — commons.wikimedia.org  (Wikipedia / Wikimedia Commons media)
  openverse  — api.openverse.org      (Creative Commons index: Flickr, Wikimedia, museums, ...)
  nasa       — images-api.nasa.gov    (NASA imagery, public domain — best for space/science/earth)
Only licenses safe for monetized, edited video are accepted: CC0, Public Domain, CC BY, CC BY-SA
(no NC / ND). Every image is converted to JPEG and credited in assets/img/CREDITS.json.

Usage:
  python tools/fetch_images.py laptop="laptop on desk" belajar="student studying"
  python tools/fetch_images.py bumi="earth from space" --providers nasa,wikimedia
  python tools/fetch_images.py --register logo-ai.png --source "AI-generated (model name)" --license "own work"
      (record an image you made yourself — AI-generated, drawn, screenshot — already placed in assets/img)

If every provider fails: rephrase the query (short, concrete, English), change --providers order,
generate the image yourself if you can, or draw the illustration in SVG/CSS instead.
"""
from __future__ import annotations

import argparse
import html
import io
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

from common import ROOT

IMG = ROOT / "assets" / "img"
CREDITS = IMG / "CREDITS.json"
UA = {"User-Agent": "motion-graphic-boilerplate/1.0 (public image fetch for video production)"}
TIMEOUT = 20
MAX_SIDE = 1600
CANDIDATES = 8  # results tried per provider before moving on
OK_LICENSES = ("cc0", "pdm", "public domain", "by")  # "by" also covers by-sa


def get(url: str, timeout: int = TIMEOUT) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def get_json(url: str) -> dict:
    return json.loads(get(url))


def license_ok(name: str) -> bool:
    """'CC BY-SA 4.0', 'by 2.0', 'cc0', 'Public domain' -> True; anything NC / ND / sampling / GFDL-only -> False."""
    n = name.lower().replace("cc-", "").replace("cc ", "").strip()
    parts = set(re.split(r"[\s-]+", n))
    if parts & {"nc", "nd"} or "sampling" in n:
        return False
    return n.startswith(OK_LICENSES)


# ---------- providers: query -> list of candidates ----------

def search_openverse(query: str) -> list[dict]:
    # license filtering server-side is slow (504s); fetch a page and filter here
    q = urllib.parse.urlencode({"q": query, "page_size": 20, "mature": "false"})
    out = []
    for r in get_json(f"https://api.openverse.org/v1/images/?{q}")["results"]:
        lic = f"{r['license']} {r.get('license_version') or ''}".strip()
        out.append({"url": r["url"], "title": r.get("title"), "author": r.get("creator") or "unknown", "license": lic,
                    "license_url": r.get("license_url"), "page": r.get("foreign_landing_url"),
                    "width": r.get("width") or 0, "height": r.get("height") or 0, "via": r.get("source")})
    return out


def search_wikimedia(query: str) -> list[dict]:
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6, "gsrlimit": 15, "prop": "imageinfo", "iiprop": "url|extmetadata|size",
        "iiurlwidth": MAX_SIDE, "iiextmetadatafilter": "LicenseShortName|Artist|LicenseUrl",
    })
    data = get_json(f"https://commons.wikimedia.org/w/api.php?{q}")
    if "error" in data:
        raise RuntimeError(data["error"].get("code", "api error"))
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        artist = re.sub(r"<[^>]+>", "", html.unescape(meta.get("Artist", {}).get("value", "unknown"))).strip()
        out.append({"url": info.get("thumburl") or info.get("url"), "title": p.get("title"), "author": artist or "unknown",
                    "license": meta.get("LicenseShortName", {}).get("value", "unknown"),
                    "license_url": meta.get("LicenseUrl", {}).get("value"), "page": info.get("descriptionurl"),
                    "width": info.get("width", 0), "height": info.get("height", 0), "via": "wikimedia"})
    return out


def search_nasa(query: str) -> list[dict]:
    q = urllib.parse.urlencode({"q": query, "media_type": "image", "page_size": 10})
    out = []
    for item in get_json(f"https://images-api.nasa.gov/search?{q}")["collection"]["items"]:
        d = item["data"][0]
        preview = next((ln["href"] for ln in item.get("links", []) if ln.get("rel") == "preview"), None)
        if not preview:
            continue
        big = preview.replace("~thumb.jpg", "~large.jpg")
        out.append({"url": big, "fallback_url": preview.replace("~thumb.jpg", "~medium.jpg"), "title": d.get("title"),
                    "author": d.get("secondary_creator") or d.get("photographer") or f"NASA {d.get('center', '')}".strip(),
                    "license": "Public Domain (NASA media guidelines)", "license_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
                    "page": f"https://images.nasa.gov/details/{d.get('nasa_id')}", "width": 0, "height": 0, "via": "nasa"})
    return out


PROVIDERS = {"openverse": search_openverse, "wikimedia": search_wikimedia, "nasa": search_nasa}


# ---------- download + normalise ----------

def save_jpeg(raw: bytes, dest: Path, min_width: int) -> tuple[int, int]:
    im = Image.open(io.BytesIO(raw))
    im.load()
    if max(im.size) < min_width:
        raise ValueError(f"too small {im.size}")
    im = im.convert("RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    im.save(dest, "JPEG", quality=90)
    return im.size


def try_provider(name: str, query: str, dest: Path, min_width: int, orientation: str) -> dict:
    found = PROVIDERS[name](query)
    usable = [c for c in found if c.get("url") and license_ok(c["license"])]
    if not usable:
        raise LookupError(f"no allowed-license results ({len(found)} total)")
    if orientation != "any":  # prefer the requested shape when the API reports sizes
        want_tall = orientation == "portrait"
        usable.sort(key=lambda c: 0 if not c["width"] else (c["height"] >= c["width"]) != want_tall)
    last = None
    for c in usable[:CANDIDATES]:
        for url in filter(None, (c["url"], c.get("fallback_url"))):
            try:
                w, h = save_jpeg(get(url, 40), dest, min_width)
                return {"provider": name, "query": query, "title": c["title"], "author": c["author"], "license": c["license"],
                        "license_url": c["license_url"], "source_page": c["page"], "via": c["via"], "size": [w, h]}
            except Exception as err:  # broken hotlink, too small, not an image -> next candidate
                last = err
    raise LookupError(f"no candidate downloadable ({type(last).__name__}: {last})")


def load_credits() -> dict:
    return json.loads(CREDITS.read_text(encoding="utf-8")) if CREDITS.exists() else {}


def fetch(wanted: dict[str, str], order: list[str], min_width: int, orientation: str) -> int:
    IMG.mkdir(parents=True, exist_ok=True)
    credits = load_credits()
    failed = []
    for stem, query in wanted.items():
        dest = IMG / f"{stem}.jpg"
        for name in order:
            try:
                credits[dest.name] = try_provider(name, query, dest, min_width, orientation)
                c = credits[dest.name]
                print(f"ok   {dest.name}  <- {name}: \"{c['title']}\" by {c['author']} ({c['license']})")
                break
            except Exception as err:  # provider down / busy / empty -> fall through to the next one
                print(f"..   {stem}: {name} failed ({type(err).__name__}: {str(err)[:90]}) -> next provider")
                time.sleep(0.5)
        else:
            failed.append(stem)
            print(f"FAIL {stem}: all providers failed for \"{query}\" — rephrase, reorder --providers, or make the image yourself")
    CREDITS.write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if failed else 0


def register(file: str, source: str, license_name: str) -> int:
    path = IMG / Path(file).name
    if not path.exists():
        raise SystemExit(f"put the file in assets/img first: {path}")
    credits = load_credits()
    credits[path.name] = {"provider": "local", "source": source, "license": license_name}
    CREDITS.write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"registered {path.name}: {source} ({license_name})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("items", nargs="*", help='stem="search query"')
    ap.add_argument("--providers", default="wikimedia,openverse,nasa", help="comma-separated order")
    ap.add_argument("--orientation", default="portrait", choices=["portrait", "landscape", "any"])
    ap.add_argument("--min-width", type=int, default=800, help="reject images whose long side is smaller")
    ap.add_argument("--register", metavar="FILE", help="credit an image you made, already in assets/img")
    ap.add_argument("--source", default="AI-generated")
    ap.add_argument("--license", default="own work")
    args = ap.parse_args()
    if args.register:
        return register(args.register, args.source, args.license)
    wanted = dict(a.split("=", 1) for a in args.items if "=" in a)
    if not wanted:
        ap.print_help()
        return 2
    order = [p.strip() for p in args.providers.split(",") if p.strip()]
    unknown = [p for p in order if p not in PROVIDERS]
    if unknown:
        raise SystemExit(f"unknown provider(s): {unknown}; choose from {list(PROVIDERS)}")
    return fetch(wanted, order, args.min_width, args.orientation)


if __name__ == "__main__":
    raise SystemExit(main())
