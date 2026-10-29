"""Draft word timings from the script alone (no dubbing yet), so scenes can be built and previewed early.

Writes build/words.json marked "estimated": true. Replace it with real timings via
tools/transcribe.py as soon as the dubbing exists — cue times WILL shift.

Usage: python tools/estimate_words.py [--wps 2.6]
"""
import argparse
import json

from common import BUILD, VOICE, WORDS, script_words

COMMA_PAUSE, SENTENCE_PAUSE, PARA_PAUSE = 0.18, 0.4, 0.7


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wps", type=float, default=2.6, help="spoken words per second (Indonesian TTS ≈ 2.4–2.8)")
    args = ap.parse_args()
    words = script_words()
    t, prev_para = 0.3, 0
    for w in words:
        if w["para"] != prev_para:
            t += PARA_PAUSE
            prev_para = w["para"]
        dur = (0.2 + 0.035 * len(w["text"])) * 2.6 / args.wps
        w.update(start=round(t, 3), end=round(t + dur, 3), estimated=True)
        t += dur + 0.04
        if w["text"][-1] in ".?!":
            t += SENTENCE_PAUSE
        elif w["text"][-1] in ",:;":
            t += COMMA_PAUSE
    BUILD.mkdir(exist_ok=True)
    WORDS.write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    VOICE.unlink(missing_ok=True)  # stale voice would not match estimated timings
    print(f"{len(words)} words, estimated length {words[-1]['end']:.1f}s -> {WORDS} (DRAFT: no dubbing)")


if __name__ == "__main__":
    main()
