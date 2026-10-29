"""Live preview in the browser: scrubber + play with the dubbing (build/voice.wav).

Usage: python tools/preview.py            # opens http://127.0.0.1:<port>/src/index.html?dev
       python tools/preview.py --t 12.5   # freeze at one moment
Edit any file in src/ and refresh the browser — no build step.
"""
import argparse
import time
import webbrowser

from common import CFG, page_url, start_server


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--t", type=float, help="freeze at this time instead of the dev scrubber")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()
    srv = start_server(CFG["render"]["port"] + 1)
    url = page_url(srv, f"?t={args.t}" if args.t is not None else "?dev")
    print(f"preview: {url}  (Ctrl+C to stop)")
    if not args.no_open:
        webbrowser.open(url)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
