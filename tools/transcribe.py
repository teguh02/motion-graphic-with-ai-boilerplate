"""Word-level timestamps for the dubbing, aligned to the script text (content/narasi.txt).

Whisper hears the audio; the script supplies the exact spelling. Each script word is mapped to a
whisper word via difflib alignment, misheard spans are spread over the heard time range, and
unmatched words are interpolated between their matched neighbours.

Then project.json "tempo" is applied: build/voice.wav (sped up, pitch kept) + build/words.json
(timestamps / tempo). atempo is a uniform stretch, so scaled timestamps stay exact.

Usage:
  python tools/transcribe.py              # whisper + align + tempo  (model from project.json)
  python tools/transcribe.py --model small
  python tools/transcribe.py --retime     # only re-apply tempo to build/words_raw.json
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import wave
from pathlib import Path

import numpy as np

from common import BUILD, CFG, ROOT, VOICE, WORDS, WORDS_RAW, ffmpeg, script_words


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def voice_path() -> Path:
    path = ROOT / CFG["audio"]["voice"]
    if not path.exists():
        raise SystemExit(f"dubbing not found: {path}\n  -> put the TTS export there, or run tools/estimate_words.py for a draft")
    return path


def load_audio_16k(path: Path) -> np.ndarray:
    """Decode any format ffmpeg reads (wav/mp3/m4a) to mono 16 kHz float32."""
    tmp = BUILD / "voice16k.wav"
    ffmpeg("-i", str(path), "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", str(tmp))
    with wave.open(str(tmp)) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return data.astype(np.float32) / 32768.0


def align(words: list[dict], heard: list) -> list[dict]:
    a = [norm(w["text"]) for w in words]
    b = [norm(w.word) for w in heard]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            for k in range(a1 - a0):
                hw = heard[b0 + k]
                words[a0 + k].update(start=hw.start, end=hw.end)
        elif op == "replace":
            # misheard span (e.g. a brand name heard as two words): spread script words over the heard range
            if a1 - a0 == b1 - b0:
                for k in range(a1 - a0):
                    words[a0 + k].update(start=heard[b0 + k].start, end=heard[b0 + k].end, fuzzy=True)
                continue
            t0, t1 = heard[b0].start, heard[b1 - 1].end
            lens = [max(1, len(norm(w["text"]))) for w in words[a0:a1]]
            acc = t0
            for k, ln in enumerate(lens):
                d = (t1 - t0) * ln / sum(lens)
                words[a0 + k].update(start=round(acc, 3), end=round(acc + d, 3), fuzzy=True)
                acc += d
    interpolate(words, heard[-1].end if heard else 0.0)
    return words


def interpolate(words: list[dict], last_end: float) -> None:
    n, i = len(words), 0
    while i < n:
        if "start" in words[i]:
            i += 1
            continue
        j = i
        while j < n and "start" not in words[j]:
            j += 1
        t0 = words[i - 1]["end"] if i > 0 else 0.0
        t1 = words[j]["start"] if j < n else max(last_end, t0 + 0.3 * (j - i))
        step = (t1 - t0) / (j - i)
        for k in range(i, j):
            words[k].update(start=round(t0 + step * (k - i), 3), end=round(t0 + step * (k - i + 1), 3), interp=True)
        i = j


def retime() -> None:
    tempo = float(CFG.get("tempo", 1.0))
    af = ["-af", f"atempo={tempo}"] if abs(tempo - 1) > 1e-6 else []
    ffmpeg("-i", str(voice_path()), *af, "-ac", "1", "-ar", "48000", str(VOICE))
    words = json.loads(WORDS_RAW.read_text(encoding="utf-8"))
    for w in words:
        w["start"] = round(w["start"] / tempo, 3)
        w["end"] = round(w["end"] / tempo, 3)
    WORDS.write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"tempo {tempo}: {len(words)} words, voice ends {words[-1]['end']:.2f}s -> {WORDS}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=CFG.get("whisper_model", "medium"))
    ap.add_argument("--retime", action="store_true", help="skip whisper, only re-apply tempo")
    args = ap.parse_args()
    BUILD.mkdir(exist_ok=True)
    if not args.retime:
        from faster_whisper import WhisperModel

        model = WhisperModel(args.model, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(load_audio_16k(voice_path()), language=CFG.get("language", "id"), word_timestamps=True)
        heard = [w for seg in segments for w in seg.words]
        print("heard:", " ".join(w.word.strip() for w in heard))
        words = align(script_words(), heard)
        WORDS_RAW.write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
        fuzzy = sum(1 for w in words if w.get("fuzzy"))
        interp = sum(1 for w in words if w.get("interp"))
        print(f"{len(words)} words aligned ({fuzzy} fuzzy, {interp} interpolated) -> {WORDS_RAW}")
    retime()


if __name__ == "__main__":
    main()
