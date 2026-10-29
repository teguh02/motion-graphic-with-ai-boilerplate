"""Shared paths, project config, local HTTP server and Playwright page loader for all tools."""
from __future__ import annotations

import functools
import http.server
import json
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OUT_DIR = ROOT / "output"
CONTENT = ROOT / "content"
SCRIPT = CONTENT / "narasi.txt"
BRIEF = CONTENT / "brief.md"
WORDS = BUILD / "words.json"
WORDS_RAW = BUILD / "words_raw.json"
VOICE = BUILD / "voice.wav"  # dubbing after tempo/resample, used by preview + final mix


def load_config() -> dict:
    return json.loads((ROOT / "project.json").read_text(encoding="utf-8"))


CFG = load_config()

# Windows consoles default to cp1252; keep non-ASCII log lines readable
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def ffmpeg_exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def ffmpeg(*args: str) -> None:
    subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", *args], check=True)


def read_paragraphs() -> list[str]:
    return [p.strip() for p in SCRIPT.read_text(encoding="utf-8").split("\n\n") if p.strip()]


def script_words() -> list[dict]:
    return [{"text": tok, "para": pi} for pi, para in enumerate(read_paragraphs()) for tok in para.split()]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args: object) -> None:  # silence request log
        pass


def start_server(port: int | None = None) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port or CFG["render"]["port"]), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def page_url(srv: http.server.ThreadingHTTPServer, query: str = "") -> str:
    return f"http://127.0.0.1:{srv.server_address[1]}/src/index.html{query}"


async def open_page(browser, srv, errors: list[str] | None = None):
    """Open the composition and wait until window.READY; raise with the page's own error otherwise."""
    page = await browser.new_page(viewport={"width": CFG["width"], "height": CFG["height"]}, device_scale_factor=1)
    errs = errors if errors is not None else []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errs.append(m.text))
    await page.goto(page_url(srv), wait_until="load")
    await page.wait_for_function("window.READY === true || window.INIT_ERROR", timeout=60000)
    init_err = await page.evaluate("window.INIT_ERROR || null")
    if init_err or errs:
        raise RuntimeError(f"page failed to init:\n{init_err or chr(10).join(errs)}")
    return page
