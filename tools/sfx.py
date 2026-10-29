"""Procedural SFX + soft ambient bed, mixed under the dubbing (no third-party audio needed).

Scenes register events with E.sfx(t, type, gain) in JS; render.py passes them to build_mix().
Add a new sound: write a function returning a mono float array at SR, register it in SYNTH,
and add its name to SFX_TYPES in src/engine.js.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from common import ffmpeg

SR = 48000
RNG = np.random.default_rng(7)


def _t(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def _env(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / decay)


def _lowpass(x: np.ndarray, cutoff: np.ndarray | float) -> np.ndarray:
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    alpha = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += alpha[i] * (x[i] - acc)
        y[i] = acc
    return y


def _sweep(f0: float, f1: float, dur: float) -> np.ndarray:
    f = np.geomspace(f0, f1, len(_t(dur)))
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def whoosh() -> np.ndarray:
    n = int(0.5 * SR)
    shape = np.sin(np.linspace(0, np.pi, n)) ** 2
    return _lowpass(RNG.standard_normal(n), np.geomspace(300, 4500, n)) * shape * 0.9


def pop() -> np.ndarray:
    return _sweep(700, 260, 0.14) * _env(int(0.14 * SR), 0.002, 0.04) * 0.9


def tick() -> np.ndarray:
    t = _t(0.05)
    return np.sin(2 * np.pi * 2300 * t) * _env(len(t), 0.001, 0.012) * 0.6


def click() -> np.ndarray:
    """Mouse click: sharp press transient, then a softer release ~70 ms later."""
    out = np.zeros(int(0.16 * SR))
    for start, amp, f in ((0.0, 1.0, 3400), (0.072, 0.55, 2700)):
        k = int(0.03 * SR)
        t = np.arange(k) / SR
        body = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.0035)
        snap = _lowpass(RNG.standard_normal(k), 6000) * np.exp(-t / 0.0018) * 0.8
        thock = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.008) * 0.6
        st = int(start * SR)
        out[st:st + k] += (body + snap + thock) * amp
    return out * 1.1


def hit() -> np.ndarray:
    n = int(0.9 * SR)
    boom = _sweep(95, 38, 0.9) * _env(n, 0.003, 0.28)
    crack = _lowpass(RNG.standard_normal(n), 2500) * _env(n, 0.001, 0.05) * 1.4
    return (boom + crack) * 0.95


def stamp() -> np.ndarray:
    n = int(0.35 * SR)
    thump = _sweep(160, 55, 0.35) * _env(n, 0.001, 0.08)
    slap = _lowpass(RNG.standard_normal(n), 1800) * _env(n, 0.0005, 0.025) * 1.6
    return thump + slap


def ding() -> np.ndarray:
    t = _t(1.0)
    e = _env(len(t), 0.002, 0.3)
    return (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t) + 0.25 * np.sin(2 * np.pi * 2637 * t)) * e * 0.4


def swell() -> np.ndarray:
    n = int(0.8 * SR)
    shape = np.linspace(0, 1, n) ** 2 * np.exp(-np.maximum(np.arange(n) / SR - 0.7, 0) / 0.05)
    tone = _sweep(180, 520, 0.8) * 0.4
    air = _lowpass(RNG.standard_normal(n), np.geomspace(500, 6000, n)) * 0.6
    return (tone + air) * shape * 0.7


def fall() -> np.ndarray:
    return _sweep(950, 180, 0.55) * _env(int(0.55 * SR), 0.01, 0.25) * 0.55


def coins() -> np.ndarray:
    out = np.zeros(int(0.7 * SR))
    for k in range(5):
        st = int((0.05 + k * 0.11) * SR)
        t = _t(0.12)
        ping = np.sin(2 * np.pi * (2600 + 400 * (k % 3)) * t) * _env(len(t), 0.001, 0.03) * 0.5
        out[st:st + len(ping)] += ping[: len(out) - st]
    return out


SYNTH = {"whoosh": whoosh, "pop": pop, "tick": tick, "click": click, "hit": hit, "stamp": stamp,
         "ding": ding, "swell": swell, "fall": fall, "coins": coins}
# lead-in so the sound's peak lands on the visual cue
OFFSET = {"whoosh": -0.22, "swell": -0.62}


def ambient_bed(n: int) -> np.ndarray:
    """Warm, slowly breathing major pad (F major add9) — sits well under speech."""
    t = np.arange(n) / SR
    freqs = [87.31, 174.61, 220.0, 261.63, 392.0]
    pad = sum(np.sin(2 * np.pi * f * t + i) * (0.6 if f < 100 else 0.22) for i, f in enumerate(freqs))
    lfo = 0.65 + 0.35 * np.sin(2 * np.pi * 0.09 * t)
    fade = np.clip(t / 1.5, 0, 1) * np.clip((t[-1] - t) / 2.5, 0, 1)
    return pad * lfo * fade


def read_wav(path: Path, build: Path) -> np.ndarray:
    tmp = build / "voice_mono48.wav"
    ffmpeg("-i", str(path), "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", str(tmp))
    with wave.open(str(tmp)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0


def build_mix(voice_path: Path | None, events: list[dict], total: float, build: Path, audio_cfg: dict) -> Path:
    """voice_path=None renders a draft with SFX + bed only (estimated timings, no dubbing yet)."""
    n = int(total * SR)
    mix = np.zeros(n, dtype=np.float64)
    if voice_path is not None and voice_path.exists():
        voice = read_wav(voice_path, build)
        peak = float(np.max(np.abs(voice))) or 1.0
        mix[: min(n, len(voice))] += voice[:n] * (0.9 / peak)
    cache: dict[str, np.ndarray] = {}
    for ev in events:
        kind = ev["type"]
        snd = cache.setdefault(kind, SYNTH[kind]())
        st = int(max(0.0, ev["t"] + OFFSET.get(kind, 0.0)) * SR)
        seg = snd[: max(0, n - st)] * audio_cfg.get("sfx_level", 0.2) * ev.get("gain", 1.0)
        mix[st:st + len(seg)] += seg
    if audio_cfg.get("bed", True):
        mix += ambient_bed(n) * audio_cfg.get("bed_level", 0.035)
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    out = build / "mix.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return out
