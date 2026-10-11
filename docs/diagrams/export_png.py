"""Export each diagram's <svg> to a PNG next to it, at 2x, with headless Chrome.

Usage: python3 docs/diagrams/export_png.py [chrome-binary]
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHROME = sys.argv[1] if len(sys.argv) > 1 else "google-chrome"
SCALE = 2

for html in sorted(HERE.glob("*.html")):
    src = html.read_text()
    fonts = re.search(r'<link href="https://fonts\.googleapis\.com[^>]*>', src).group(0)
    svg = re.search(r"<svg\b.*?</svg>", src, re.S).group(0)
    w, h = map(int, re.search(r'viewBox="0 0 (\d+) (\d+)"', svg).groups())
    page = (f'<!DOCTYPE html><html><head><meta charset="UTF-8">{fonts}'
            f'<style>html,body{{margin:0;background:transparent}}svg{{display:block;width:{w}px;height:{h}px}}</style>'
            f'</head><body>{svg}</body></html>')
    with tempfile.TemporaryDirectory() as tmp:
        wrapper = Path(tmp) / "page.html"
        wrapper.write_text(page)
        out = html.with_suffix(".png")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--default-background-color=00000000", f"--force-device-scale-factor={SCALE}",
                        f"--window-size={w},{h}", "--virtual-time-budget=8000",
                        f"--screenshot={out}", wrapper.as_uri()],
                       check=True, capture_output=True)
        print(out.relative_to(HERE.parent.parent))
