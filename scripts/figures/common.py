"""Shared helpers for the animated README figures.

A Figure collects SVG elements and per-element CSS keyframes on one shared
loop. Each animated element follows a list of (seconds, opacity) points, so a
figure's timeline reads top to bottom like a script.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "assets" / "figures"

MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'
SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
FADE = 0.15

THEME = f"""
  .card {{ fill: #f6f8fa; stroke: #d1d9e0; }}
  text {{ font-family: {SANS}; font-size: 12px; fill: #1f2328; }}
  .h {{ font-size: 15px; font-weight: 600; }}
  .m {{ font-size: 12px; fill: #59636e; }}
  .cap {{ font-size: 13px; }}
  .s {{ font-size: 11px; fill: #59636e; }}
  .b {{ font-weight: 600; }}
  .lbl {{ font-size: 10px; font-weight: 600; letter-spacing: .08em; fill: #59636e; }}
  .code {{ font-family: {MONO}; font-size: 13px; }}
  .sm {{ font-size: 11.5px; }}
  .box, .chip, .node, .rung {{ fill: #ffffff; stroke: #d1d9e0; }}
  .rung {{ stroke: #e1e6eb; }}
  .node {{ stroke: #0969da; }}
  .hl {{ fill: #0969da; fill-opacity: .14; stroke: #0969da; stroke-opacity: .6; }}
  .bad {{ fill: #cf222e; fill-opacity: .12; stroke: #cf222e; }}
  .badt {{ fill: #cf222e; }}
  .ok {{ fill: #1a7f37; }}
  .edge {{ stroke: #8c959f; stroke-width: 1.5; fill: none; }}
  .tip {{ fill: #8c959f; }}
  .term {{ fill: #1f2328; }}
  .termt {{ fill: #e6edf3; }}
  .termerr {{ fill: #ff7b72; }}
  .termdim {{ fill: #9198a1; }}
  .termok {{ fill: #3fb950; }}
  .k {{ fill: #cf222e; }} .f {{ fill: #8250df; }} .str {{ fill: #0a3069; }} .num {{ fill: #0550ae; }} .cm {{ fill: #6e7781; }}
  @media (prefers-color-scheme: dark) {{
    .card {{ fill: #151b23; stroke: #3d444d; }}
    text {{ fill: #e6edf3; }}
    .m, .s, .lbl {{ fill: #9198a1; }}
    .box, .chip, .node, .rung {{ fill: #0d1117; stroke: #3d444d; }}
    .node {{ stroke: #4493f8; }}
    .hl {{ fill: #4493f8; stroke: #4493f8; }}
    .bad {{ fill: #f85149; stroke: #f85149; }}
    .badt {{ fill: #ff7b72; }}
    .ok {{ fill: #3fb950; }}
    .edge {{ stroke: #656c76; }}
    .tip {{ fill: #656c76; }}
    .term {{ fill: #010409; }}
    .k {{ fill: #ff7b72; }} .f {{ fill: #d2a8ff; }} .str {{ fill: #a5d6ff; }} .num {{ fill: #79c0ff; }} .cm {{ fill: #8b949e; }}
  }}
"""


class Figure:
    def __init__(self, name, width, height, period, label):
        self.name, self.w, self.h, self.period, self.label = name, width, height, period, label
        self.css, self.body = [], []

    # ── animation ────────────────────────────────────────────────────────────
    def track(self, points):
        """Return a class whose opacity follows [(seconds, opacity), ...] each loop."""
        name = f"a{len(self.css)}"
        frames = []
        for i, (t, v) in enumerate(points):
            pct = t / self.period * 100
            if i and points[i - 1][1] != v:
                frames.append(f"{min(pct, 100):.2f}% {{ opacity: {points[i - 1][1]}; }}")
                pct += FADE / self.period * 100
            frames.append(f"{min(pct, 100):.2f}% {{ opacity: {v}; }}")
        self.css.append(f".{name} {{ animation: {name} {self.period}s infinite; }}\n"
                        f"@keyframes {name} {{ {' '.join(frames)} }}")
        return name

    def window(self, start, end):
        """Visible from start to end, hidden otherwise."""
        return self.track([(0, 0), (start, 1), (end, 0), (self.period, 0)])

    # ── drawing ──────────────────────────────────────────────────────────────
    def add(self, svg):
        self.body.append(svg)

    def text(self, x, y, s, cls="", anchor="start"):
        self.add(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{escape(s)}</text>')

    def runs(self, x, y, parts, cls="code"):
        """One line of text built from (class, text) runs."""
        spans = "".join(f'<tspan class="{c}">{escape(t)}</tspan>' if c else escape(t) for c, t in parts)
        self.add(f'<text x="{x}" y="{y}" class="{cls}" xml:space="preserve">{spans}</text>')

    def header(self, title, subtitle):
        self.add(f'<rect class="card" x="0.5" y="0.5" width="{self.w - 1}" height="{self.h - 1}" rx="8"/>')
        self.text(20, 34, title, "h")
        self.text(20, 54, subtitle, "m")

    def arrow(self, d, cls=""):
        self.add(f'<path class="edge {cls}" d="{d}" marker-end="url(#arr)"/>')

    # ── output ───────────────────────────────────────────────────────────────
    def write(self):
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.label)}">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" class="tip"/></marker></defs>
<style>{THEME}
{chr(10).join(self.css)}
  @media (prefers-reduced-motion: reduce) {{
    [class^="a"], [class*=" a"] {{ animation: none !important; opacity: 1; }}
    .hl, .cap {{ display: none; }}
  }}
</style>
{chr(10).join(self.body)}
</svg>
"""
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / f"{self.name}.svg"
        path.write_text(svg)
        print(f"wrote {path.relative_to(ROOT)} ({len(svg) // 1024} KB)")
        return path
