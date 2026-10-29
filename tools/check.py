"""QA before rendering. Exit code 0 = PASS. Checks:
  1. page boots with no JS errors (missing cue words, icons, images surface here)
  2. every visible text box (outside [data-safe-ignore]) stays inside the Reels/TikTok safe zone (project.json safe_zone)
  3. karaoke subtitles highlight each word at its own timestamp
  4. text in [data-verbatim] elements (code blocks) exists verbatim in content/brief.md
  5. scenes are contiguous (no gaps / long overlaps)

Usage: python tools/check.py [--step 0.25]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re

from playwright.async_api import async_playwright

from common import BRIEF, CFG, WORDS, open_page, start_server

JS_SAFE = """(s) => {
  const bad = [];
  document.querySelectorAll('#frame *').forEach((el) => {
    if (el.closest('[data-safe-ignore]')) return;
    if (![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) return;
    let o = 1, p = el;
    while (p && p.id !== 'frame') {
      const cs = getComputedStyle(p);
      if (cs.visibility === 'hidden' || cs.display === 'none') return;
      o *= +cs.opacity; p = p.parentElement;
    }
    if (o < 0.5) return;
    const rg = document.createRange(); rg.selectNodeContents(el); const r = rg.getBoundingClientRect();
    if (!r.width) return;
    const right = r.bottom > s.low_y ? s.W - s.right_low : s.W - s.right;
    if (r.top < s.top || r.bottom > s.H - s.bottom || r.left < s.left || r.right > right)
      bad.push(`"${el.textContent.trim().slice(0, 30)}" [${r.left | 0},${r.top | 0},${r.right | 0},${r.bottom | 0}]`);
  });
  return bad;
}"""

JS_VERBATIM = """() => [...document.querySelectorAll('[data-verbatim]')].flatMap((pre) => {
  const lines = pre.querySelectorAll('.ln').length
    ? [...pre.querySelectorAll('.ln .tx')].map((x) => x.textContent)
    : pre.textContent.split('\\n');
  return lines.filter((l) => l.trim()).map((l) => l.replace(/\\s+$/, ''));
})"""

JS_ACTIVE = """() => [...document.querySelectorAll('.chunk .w.on')]
  .filter((e) => +e.parentElement.style.opacity > .5).map((e) => e.textContent)"""


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


async def run(step: float) -> int:
    problems = 0
    errors: list[str] = []
    safe = {**CFG["safe_zone"], "W": CFG["width"], "H": CFG["height"]}
    if not WORDS.exists():
        print("FAIL: build/words.json missing -> python tools/transcribe.py (or tools/estimate_words.py)")
        return 1
    words = json.loads(WORDS.read_text(encoding="utf-8"))
    renamed = {norm(k) for k in CFG["subtitles"].get("rename", {})}
    srv = start_server()
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            try:
                page = await open_page(browser, srv, errors)
            except RuntimeError as err:
                print(f"FAIL boot: {err}")
                return 1
            total = await page.evaluate("window.TOTAL")
            scenes = await page.evaluate("window.SCENE_TIMES")
            print(f"total {total}s, {len(scenes)} scenes:", ", ".join(f"{s['id']} {s['start']}-{s['end']}" for s in scenes))

            # 5. scene continuity
            for a, b in zip(scenes, scenes[1:]):
                if b["start"] - a["end"] > 0.05 or a["end"] - b["start"] > 0.5:
                    print(f"WARN scene gap/overlap: {a['id']} ends {a['end']} / {b['id']} starts {b['start']}")
            if scenes and scenes[-1]["end"] < total - 0.05:
                print(f"WARN last scene ends {scenes[-1]['end']} before TOTAL {total}")

            # 2. safe zone
            issues: dict[float, list[str]] = {}
            t = 0.0
            while t < total:
                await page.evaluate("t => renderAt(t)", t)
                bad = await page.evaluate(JS_SAFE, safe)
                if bad:
                    issues[round(t, 2)] = bad
                t += step
            print(f"safe zone: {'OK' if not issues else f'{len(issues)} frame(s) with text outside'}")
            for k, v in list(issues.items())[:15]:
                print(f"  t={k}: {v[:3]}")
            problems += bool(issues)

            # 3. subtitle sync
            miss = []
            for w in words:
                if norm(w["text"]) in renamed:
                    continue
                mid = (w["start"] + w["end"]) / 2
                await page.evaluate("t => renderAt(t)", mid)
                on = [norm(x) for x in await page.evaluate(JS_ACTIVE)]
                if norm(w["text"]) not in on:
                    miss.append((w["text"], round(mid, 2), on))
            print(f"subtitle sync: {len(words) - len(miss)}/{len(words)} words highlighted on time")
            for m in miss[:10]:
                print("  miss", m)
            problems += bool(miss)

            # 4. verbatim text
            await page.evaluate("t => renderAt(t)", total - 0.01)
            lines = await page.evaluate(JS_VERBATIM)
            brief = BRIEF.read_text(encoding="utf-8") if BRIEF.exists() else ""
            brief_lines = {ln.rstrip() for ln in brief.splitlines()} | {ln.strip() for ln in brief.splitlines()}
            for ln in sorted(set(lines)):
                ok = ln in brief_lines or ln.strip() in brief_lines or ln.strip() in brief
                if not ok:
                    print(f"MISS verbatim (not in brief.md): {ln}")
                problems += not ok
            print(f"verbatim: {len(set(lines))} line(s) checked")

            # 1. runtime errors during the sweep
            if errors:
                print("FAIL page errors:", *errors[:10], sep="\n  ")
                problems += 1
            await browser.close()
    finally:
        srv.shutdown()
    if any(w.get("estimated") for w in words):
        print("NOTE: timings are ESTIMATED (no dubbing yet) — rerun after tools/transcribe.py")
    print("check:", "PASS" if not problems else f"{problems} problem group(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=float, default=0.25, help="seconds between safe-zone samples")
    raise SystemExit(asyncio.run(run(ap.parse_args().step)))
