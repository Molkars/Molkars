#!/usr/bin/env python3
"""Stitch every animated figure into one looping GIF per theme.

    python3 scripts/figures/gif.py   # writes assets/figures.gif and assets/figures-dark.gif

Each figure's CSS keyframes are evaluated at a fixed frame rate and baked into
static SVGs, which headless Chromium screenshots in batches. Runs of identical
frames collapse into one longer GIF frame, so the long holds cost nothing.
Needs Chromium and Pillow.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import OUT_DIR, ROOT  # noqa: E402

# Order the figures appear in, matching the README.
FIGURES = ["bytecode", "notch-templates", "notch-commands", "notch-syntax",
           "notch-traces", "sea-c", "sea-lmsm", "grading"]
FPS = 20
SCALE = 1.5           # pixel density of the GIF relative to the 780px layout
W, H = 780, 656       # figure area; taller figures are scaled down to fit
DOTS = 28             # height of the progress strip under the figure
BATCH = 12            # frames per Chromium screenshot
PAGE = {"light": "#ffffff", "dark": "#0d1117"}
DOT = {"light": ("#0969da", "#d1d9e0"), "dark": ("#4493f8", "#3d444d")}

ANIM = re.compile(r"\.(a\d+) \{ animation: \1 ([\d.]+)s infinite; \}\n@keyframes \1 \{ (.*?) \}\n")
STOP = re.compile(r"([\d.]+)% \{ opacity: ([\d.]+); \}")


def block(css, head):
    """Return (start, end, inner) of the brace block that follows `head`."""
    start = css.index(head)
    i = css.index("{", start) + 1
    depth = 1
    for j in range(i, len(css)):
        depth += {"{": 1, "}": -1}.get(css[j], 0)
        if not depth:
            return start, j + 1, css[i:j]
    raise ValueError(head)


def load(name, theme):
    """Return (svg template with a {state} hole, tracks, period)."""
    svg = (OUT_DIR / f"{name}.svg").read_text()
    tracks, period = {}, 0.0
    for cls, p, stops in ANIM.findall(svg):
        period = float(p)
        tracks[cls] = [(float(pct) / 100 * period, float(v)) for pct, v in STOP.findall(stops)]
    svg = ANIM.sub("", svg)
    a, b, _ = block(svg, "@media (prefers-reduced-motion")
    svg = svg[:a] + svg[b:]
    while "@media (prefers-color-scheme: dark)" in svg:
        a, b, inner = block(svg, "@media (prefers-color-scheme: dark)")
        svg = svg[:a] + (inner if theme == "dark" else "") + svg[b:]
    svg = svg.replace("{", "{{").replace("}", "}}").replace("</style>", "{state}</style>", 1)
    return svg, tracks, period


def opacity(stops, t):
    for (t0, v0), (t1, v1) in zip(stops, stops[1:]):
        if t0 <= t <= t1:
            return v0 if t1 == t0 else v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return stops[-1][1]


def frames(name, theme):
    """Yield (svg, size, seconds) with consecutive identical frames merged."""
    svg, tracks, period = load(name, theme)
    size = re.search(r'width="(\d+)" height="(\d+)"', svg).groups()
    last, held = None, 0
    for i in range(round(period * FPS)):
        state = tuple(round(opacity(s, i / FPS), 2) for s in tracks.values())
        if state != last and last is not None:
            yield last_svg, size, held / FPS
            held = 0
        if state != last:
            css = "\n".join(f".{c} {{ opacity: {v}; }}" for c, v in zip(tracks, state))
            last, last_svg = state, svg.format(state=css)
        held += 1
    yield last_svg, size, held / FPS


def page(batch, theme):
    """One HTML page stacking a batch of frames, each centered in the canvas."""
    on, off = DOT[theme]
    cells = []
    for svg, (w, h), index in batch:
        s = min(1, W / int(w), H / int(h))
        dots = "".join(f'<i style="background:{on if k == index else off}"></i>' for k in range(len(FIGURES)))
        cells.append(f'<div class="f"><div class="fig" style="width:{int(w) * s}px;height:{int(h) * s}px">'
                     f'<div style="transform:scale({s});transform-origin:0 0">{svg}</div></div>'
                     f'<div class="dots">{dots}</div></div>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
  html, body {{ margin: 0; background: {PAGE[theme]}; }}
  .f {{ width: {W}px; height: {H + DOTS}px; display: flex; flex-direction: column; align-items: center; }}
  .fig {{ height: {H}px; flex: 0 0 auto; margin: auto 0 0; overflow: hidden; }}
  .dots {{ height: {DOTS}px; flex: 0 0 auto; display: flex; gap: 8px; align-items: center; }}
  .dots i {{ width: 6px; height: 6px; border-radius: 50%; }}
  svg {{ display: block; }}
</style></head><body>{''.join(cells)}</body></html>"""


def shoot(chromium, html, out, n):
    html.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([chromium, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                    f"--force-device-scale-factor={SCALE}", "--force-color-profile=srgb",
                    f"--window-size={W},{(H + DOTS) * n}", f"--screenshot={out}", html.as_uri()],
                   check=True, capture_output=True)


def build(theme, chromium, tmp):
    items = []  # (svg, size, figure index, seconds)
    for index, name in enumerate(FIGURES):
        items += [(svg, size, index, sec) for svg, size, sec in frames(name, theme)]
    batches = [items[i:i + BATCH] for i in range(0, len(items), BATCH)]
    jobs = []
    for b, batch in enumerate(batches):
        html = tmp / theme / f"{b}.html"
        html.parent.mkdir(parents=True, exist_ok=True)
        html.write_text(page([(svg, size, index) for svg, size, index, _ in batch], theme))
        jobs.append((html, tmp / theme / f"{b}.png", len(batch)))
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda j: shoot(chromium, *j), jobs))

    fw, fh = round(W * SCALE), round((H + DOTS) * SCALE)
    images, durations = [], []
    for (_, png, n), batch in zip(jobs, batches):
        sheet = Image.open(png).convert("RGB")
        for k, (*_, sec) in enumerate(batch):
            images.append(sheet.crop((0, k * fh, fw, (k + 1) * fh)))
            durations.append(round(sec * 1000))

    # One shared palette keeps colors stable from frame to frame.
    sample = Image.new("RGB", (fw, fh * 8))
    for k, im in enumerate(images[:: max(1, len(images) // 8)][:8]):
        sample.paste(im, (0, k * fh))
    palette = sample.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    frames_p = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in images]

    out = ROOT / "assets" / ("figures.gif" if theme == "light" else "figures-dark.gif")
    frames_p[0].save(out, save_all=True, append_images=frames_p[1:], duration=durations,
                     loop=0, optimize=True, disposal=1)
    total = sum(durations) / 1000
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB, {len(images)} frames, {total:.0f}s)")


def main():
    chromium = next(filter(None, map(shutil.which, ["chromium-browser", "chromium", "google-chrome"])), None)
    if not chromium:
        sys.exit("needs Chromium on PATH")
    with tempfile.TemporaryDirectory() as tmp:
        for theme in ("light", "dark"):
            build(theme, chromium, Path(tmp))


if __name__ == "__main__":
    main()
