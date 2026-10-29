"""Environment + project readiness check. Run first on a fresh clone; agents run it before every phase.

Usage: python tools/doctor.py
"""
from __future__ import annotations

import importlib
import json
import sys

from common import BRIEF, CFG, ROOT, SCRIPT, VOICE, WORDS

OK, WARN, FAIL = "ok  ", "WARN", "FAIL"


def line(status: str, msg: str) -> bool:
    print(f"[{status}] {msg}")
    return status != FAIL


def main() -> int:
    good = True
    good &= line(OK if sys.version_info >= (3, 10) else FAIL, f"python {sys.version.split()[0]} (need 3.10+)")
    for mod, why in (("playwright", "render/check"), ("imageio_ffmpeg", "ffmpeg binary"), ("numpy", "audio"),
                     ("PIL", "contact sheets"), ("faster_whisper", "transcribe")):
        try:
            importlib.import_module(mod)
            line(OK, f"{mod} ({why})")
        except ImportError:
            good &= line(FAIL if mod != "faster_whisper" else WARN, f"{mod} missing ({why}) -> pip install -r requirements.txt")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            pw.chromium.launch().close()
        line(OK, "chromium for playwright")
    except Exception as err:  # browser not installed yet
        good &= line(FAIL, f"chromium not ready ({type(err).__name__}) -> python -m playwright install chromium")

    for f in ("PlusJakartaSans.woff2", "JetBrainsMono-1.woff2", "JetBrainsMono-2.woff2"):
        good &= line(OK if (ROOT / "assets" / "fonts" / f).exists() else FAIL, f"font {f}")

    good &= line(OK if SCRIPT.exists() and SCRIPT.read_text(encoding="utf-8").strip() else FAIL, f"script {SCRIPT.relative_to(ROOT)}")
    line(OK if BRIEF.exists() else WARN, f"brief {BRIEF.relative_to(ROOT)}")
    voice = ROOT / CFG["audio"]["voice"]
    line(OK if voice.exists() else WARN, f"dubbing {CFG['audio']['voice']}" + ("" if voice.exists() else " missing (TTS not done yet)"))
    if WORDS.exists():
        words = json.loads(WORDS.read_text(encoding="utf-8"))
        est = any(w.get("estimated") for w in words)
        line(WARN if est else OK, f"timings build/words.json: {len(words)} words, ends {words[-1]['end']:.1f}s" + (" (ESTIMATED)" if est else ""))
        if voice.exists() and est:
            line(WARN, "dubbing exists but timings are estimated -> python tools/transcribe.py")
    else:
        line(WARN, "build/words.json missing -> tools/transcribe.py (or tools/estimate_words.py for a draft)")
    line(OK if VOICE.exists() else WARN, "build/voice.wav" + ("" if VOICE.exists() else " missing (created by transcribe.py)"))
    print("doctor:", "READY" if good else "fix FAIL items first")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
