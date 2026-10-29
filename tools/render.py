"""Render src/index.html frame-by-frame with Playwright, encode with ffmpeg, mix dubbing + SFX.

Usage:
  python tools/render.py --stills 1.0,7.5,12      # PNGs into build/stills (fast visual check)
  python tools/render.py --scenes                 # 3 stills per scene + contact sheet build/sheet_*.jpg
  python tools/render.py                          # full render -> output/<project.json output>
  python tools/render.py --draft                  # full render, half resolution, fast (preview only)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import shutil
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright

from common import BUILD, CFG, OUT_DIR, VOICE, WORDS, ffmpeg, ffmpeg_exe, open_page, start_server
from contact import contact_sheets
from sfx import build_mix

FPS = CFG["fps"]
RCFG = CFG["render"]


async def render_stills(srv, times: list[float], clear: bool = True) -> Path:
    out = BUILD / "stills"
    if clear and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await open_page(browser, srv)
        for t in times:
            await page.evaluate("t => renderAt(t)", t)
            await page.screenshot(path=str(out / f"t_{t:06.2f}.png"))
        print(json.dumps(await page.evaluate("window.SCENE_TIMES"), indent=0))
        await browser.close()
    print(f"{len(times)} stills -> {out}")
    return out


async def scene_times(srv) -> list[dict]:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await open_page(browser, srv)
        scenes = await page.evaluate("window.SCENE_TIMES")
        await browser.close()
    return scenes


def ffmpeg_chunk(path: Path, scale: float) -> subprocess.Popen:
    vf = "scale=in_range=pc:out_range=tv,format=yuv420p"
    if scale != 1:
        vf = f"scale=iw*{scale}:ih*{scale}:in_range=pc:out_range=tv,format=yuv420p"
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
           "-vf", vf, "-color_range", "tv", "-colorspace", "bt709",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(RCFG["crf"]), "-r", str(FPS), str(path)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


async def worker(browser, srv, idx: int, frames: range, part: Path, progress: dict, scale: float) -> None:
    page = await open_page(browser, srv)
    proc = ffmpeg_chunk(part, scale)
    try:
        for f in frames:
            await page.evaluate("t => renderAt(t)", f / FPS)
            buf = await page.screenshot(type="jpeg", quality=RCFG["jpeg_quality"])
            await asyncio.to_thread(proc.stdin.write, buf)
            progress[idx] += 1
    finally:
        proc.stdin.close()
        await asyncio.to_thread(proc.wait)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg chunk {idx} failed")


async def render_video(srv, scale: float) -> tuple[Path, list[dict], float]:
    chunks = BUILD / "chunks"
    chunks.mkdir(parents=True, exist_ok=True)
    workers = max(1, int(RCFG["workers"]))
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        probe = await open_page(browser, srv)
        total = await probe.evaluate("window.TOTAL")
        sfx_events = await probe.evaluate("window.SFX_EVENTS")
        await probe.close()
        n = math.ceil(total * FPS)
        per = math.ceil(n / workers)
        ranges = [range(i * per, min(n, (i + 1) * per)) for i in range(workers)]
        parts = [chunks / f"part_{i}.mp4" for i in range(workers) if len(ranges[i])]
        progress = {i: 0 for i in range(len(parts))}

        async def report() -> None:
            t0 = time.time()
            while sum(progress.values()) < n:
                await asyncio.sleep(15)
                done = sum(progress.values())
                print(f"  {done}/{n} frames ({done / max(1e-6, time.time() - t0):.1f} fps)", flush=True)

        rep = asyncio.create_task(report())
        await asyncio.gather(*(worker(browser, srv, i, ranges[i], parts[i], progress, scale) for i in range(len(parts))))
        rep.cancel()
        await browser.close()

    listing = chunks / "list.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    silent = BUILD / "video_silent.mp4"
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(silent))
    return silent, sfx_events, total


def mux(silent: Path, audio: Path, out: Path) -> None:
    lufs = CFG["audio"].get("loudness_lufs", -14)
    ffmpeg("-i", str(silent), "-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
           "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11,volume=2.2dB,alimiter=limit=0.78", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
           "-shortest", "-movflags", "+faststart", str(out))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", help="comma-separated times in seconds")
    ap.add_argument("--scenes", action="store_true", help="stills at 20/55/90%% of every scene + contact sheet")
    ap.add_argument("--draft", action="store_true", help="half-resolution full render")
    args = ap.parse_args()
    estimated = any(w.get("estimated") for w in json.loads(WORDS.read_text(encoding="utf-8"))) if WORDS.exists() else False
    srv = start_server()
    try:
        if args.stills:
            asyncio.run(render_stills(srv, [float(x) for x in args.stills.split(",")]))
            return
        if args.scenes:
            scenes = asyncio.run(scene_times(srv))
            times = [round(sc["start"] + (sc["end"] - sc["start"]) * k, 2) for sc in scenes for k in (0.2, 0.55, 0.9)]
            out = asyncio.run(render_stills(srv, times))
            for sheet in contact_sheets(out, BUILD / "sheet", per=12):
                print(f"contact sheet -> {sheet}")
            return
        t0 = time.time()
        silent, events, total = asyncio.run(render_video(srv, 0.5 if args.draft else 1))
        print(f"video frames done in {time.time() - t0:.0f}s; mixing audio ({len(events)} sfx)")
        if estimated or not VOICE.exists():
            print("WARNING: no dubbing (build/voice.wav) — rendering a DRAFT with SFX only")
        OUT_DIR.mkdir(exist_ok=True)
        mix = build_mix(VOICE if VOICE.exists() and not estimated else None, events, total, BUILD, CFG["audio"])
        name = CFG["output"] if not args.draft else Path(CFG["output"]).stem + "_draft.mp4"
        mux(silent, mix, OUT_DIR / name)
        print(f"done -> {OUT_DIR / name}")
    finally:
        srv.shutdown()


if __name__ == "__main__":
    main()
