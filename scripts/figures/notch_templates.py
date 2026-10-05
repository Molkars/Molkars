#!/usr/bin/env python3
"""Animated figure: Notch template layouts, rendered in two passes.

Writes assets/figures/notch-templates.svg. The templates, rendered output, and
diagnostic are taken from running them through Notch itself.
"""
from common import Figure

W, H = 780, 622
fig = Figure("notch-templates", W, H, period=17.0, label=(
    "Diagram of layouts in Sunny, Notch's template engine. index.html declares #layout :base.html and fills the title "
    "block. Pass 1 registers base.html's slots and checks the child's block names; pass 2 renders "
    "the child into a blocks map, then renders the layout with the slots filled, producing a page "
    "with the title 'Home | My App' and 'Hello, world!'. A misspelled block name fails in pass 1 "
    "with a diagnostic pointing at the line."))
HOLD = 16.3


def until_hold(t):
    return fig.window(t, HOLD)


fig.header("Sunny — layouts in two passes",
           "Layout and content blocks I wrote for Sunny, the template engine in Notch (MSU's scripting "
           "language): check every slot, then render.")

# ── Pass indicator ───────────────────────────────────────────────────────────
PASS_Y = 72
for i, (label, start, end) in enumerate([("PASS 1 · preRender: register and check slots", 0.3, 5.0),
                                         ("PASS 2 · render: child into blocks, then layout", 5.0, 11.0)]):
    x = 20 + i * 374
    fig.add(f'<rect class="chip" x="{x}" y="{PASS_Y}" width="366" height="26" rx="13"/>')
    fig.add(f'<rect class="hl {fig.window(start, end)}" x="{x}" y="{PASS_Y}" width="366" height="26" rx="13"/>')
    fig.text(x + 183, PASS_Y + 17, label, "sm b", "middle")

# ── Panels ───────────────────────────────────────────────────────────────────
PANEL_Y, PANEL_H = 128, 196
CHILD_X, CHILD_W = 20, 244
MAP_X, MAP_W = 276, 228
LAY_X, LAY_W = 516, 244
fig.text(CHILD_X, PANEL_Y - 8, "CHILD  index.html", "lbl")
fig.text(MAP_X, PANEL_Y - 8, "BLOCKS  (shared map)", "lbl")
fig.text(LAY_X, PANEL_Y - 8, "LAYOUT  base.html", "lbl")
for x, w in ((CHILD_X, CHILD_W), (MAP_X, MAP_W), (LAY_X, LAY_W)):
    fig.add(f'<rect class="box" x="{x}" y="{PANEL_Y}" width="{w}" height="{PANEL_H}" rx="6"/>')

LINE_H = 22


def code_lines(x, w, lines, active):
    """Draw numbered template lines; `active` maps line number -> [(start, end), ...]."""
    for n, spans in active.items():
        for start, end in spans:
            y = PANEL_Y + 10 + (n - 1) * LINE_H
            fig.add(f'<rect class="hl {fig.window(start, end)}" x="{x + 4}" y="{y}" width="{w - 8}" '
                    f'height="{LINE_H - 2}" rx="3"/>')
    for n, parts in enumerate(lines, 1):
        fig.runs(x + 10, PANEL_Y + 10 + (n - 1) * LINE_H + 15, [("cm", f"{n} ")] + parts, "code sm")


CMD, TAG, STR = "k", "f", "str"
code_lines(CHILD_X, CHILD_W, [
    [(CMD, "#layout "), (STR, ":base.html")],
    [(CMD, "#content "), ("", "title "), (CMD, "with")],
    [(TAG, "  <title>"), ("", "Home | My App"), (TAG, "</title>")],
    [(CMD, "#end")],
    [(TAG, "<main>"), ("", "Hello, "), ("num", "${ name }"), ("", "!"), (TAG, "</main>")],
], {1: [(0.3, 1.2)], 2: [(2.9, 3.9)], 3: [(5.0, 6.0)], 5: [(6.2, 7.6)]})

code_lines(LAY_X, LAY_W, [
    [(TAG, "<head>")],
    [(CMD, "#content "), ("", "title "), (CMD, "with")],
    [(TAG, "  <title>"), ("", "My App"), (TAG, "</title>")],
    [(CMD, "#end")],
    [(TAG, "</head>")],
    [(TAG, "<body>")],
    [(CMD, "#content")],
    [(TAG, "</body>")],
], {2: [(1.2, 2.0), (8.4, 9.0)], 7: [(2.0, 2.8), (9.6, 10.1)],
    1: [(8.0, 8.4)], 5: [(9.0, 9.3)], 6: [(9.3, 9.6)], 8: [(10.1, 10.5)]})

# Blocks map: one row per slot, key on top, value below.
ROWS = [
    ("title", 1.6, 5.6, "<title>Home | My App</title>", [(8.4, 9.0)]),
    ("<body>", 2.4, 7.2, "<main>Hello, world!</main>", [(9.6, 10.1)]),
]
for i, (key, t_reg, t_fill, value, uses) in enumerate(ROWS):
    y = PANEL_Y + 12 + i * 62
    fig.add(f'<g class="{until_hold(t_reg)}"><rect class="chip" x="{MAP_X + 8}" y="{y}" width="{MAP_W - 16}" '
            f'height="52" rx="5"/><text x="{MAP_X + 18}" y="{y + 19}" class="code sm b">{key.replace("<", "&lt;").replace(">", "&gt;")}</text></g>')
    for start, end in uses:
        fig.add(f'<rect class="hl {fig.window(start, end)}" x="{MAP_X + 8}" y="{y}" width="{MAP_W - 16}" height="52" rx="5"/>')
    fig.add(f'<text x="{MAP_X + 18}" y="{y + 40}" class="s {fig.window(t_reg, t_fill)}">empty slot</text>')
    fig.add(f'<text x="{MAP_X + 18}" y="{y + 40}" class="code xs {until_hold(t_fill)}">'
            f'{value.replace("<", "&lt;").replace(">", "&gt;")}</text>')
fig.css.append(".xs { font-size: 11px; }")
# Pass-1 check on the child's #content title
fig.add(f'<text x="{MAP_X + MAP_W - 18}" y="{PANEL_Y + 31}" class="b ok {fig.window(3.3, 5.0)}" text-anchor="end">'
        f'✓ exists</text>')
# ${ name } evaluation
fig.add(f'<g class="{fig.window(6.6, 7.6)}"><rect class="chip" x="{MAP_X + 8}" y="{PANEL_Y + 140}" width="{MAP_W - 16}" '
        f'height="40" rx="5"/><text x="{MAP_X + 18}" y="{PANEL_Y + 158}" class="s">evaluate with the full parser:</text>'
        f'<text x="{MAP_X + 18}" y="{PANEL_Y + 173}" class="code xs">${{ name }} → "world"</text></g>')

# ── Output ───────────────────────────────────────────────────────────────────
OUT_Y, OUT_H = 362, 186
OUT_X, OUT_W = 20, 346
fig.text(OUT_X, OUT_Y - 8, "RENDERED OUTPUT", "lbl")
fig.add(f'<rect class="box" x="{OUT_X}" y="{OUT_Y}" width="{OUT_W}" height="{OUT_H}" rx="6"/>')
OUTPUT = [
    (8.0, [(TAG, "<head>")]),
    (8.4, [(TAG, "  <title>"), ("", "Home | My App"), (TAG, "</title>")]),
    (9.0, [(TAG, "</head>")]),
    (9.3, [(TAG, "<body>")]),
    (9.6, [(TAG, "<main>"), ("", "Hello, world!"), (TAG, "</main>")]),
    (10.1, [(TAG, "</body>")]),
]
for i, (t, parts) in enumerate(OUTPUT):
    y = OUT_Y + 26 + i * 24
    spans = "".join(f'<tspan class="{c}">{s.replace("<", "&lt;").replace(">", "&gt;")}</tspan>' if c
                    else s.replace("<", "&lt;").replace(">", "&gt;") for c, s in parts)
    fig.add(f'<text x="{OUT_X + 12}" y="{y}" class="code sm {until_hold(t)}" xml:space="preserve">{spans}</text>')

# ── Diagnostic ───────────────────────────────────────────────────────────────
DX, DW = 380, 380
fig.text(DX, OUT_Y - 8, "AND IF A BLOCK NAME IS WRONG …", "lbl")
fig.add(f'<rect class="term" x="{DX}" y="{OUT_Y}" width="{DW}" height="{OUT_H}" rx="6"/>')
DIAG = [
    (11.0, "termdim", "#content footer with   (in bad.html)"),
    (11.6, "termt", "   --> bad.html:2:1"),
    (11.6, "termt", "    |"),
    (11.6, "termt", "  2 | #content footer with"),
    (11.9, "termerr", "    | ^^^^^^^^"),
    (11.9, "termt", "    |"),
    (12.3, "termerr", 'note: no block named "footer" in the layout'),
    (12.3, "termerr", "      template"),
]
for i, (t, cls, s) in enumerate(DIAG):
    y = OUT_Y + 24 + i * 20
    fig.add(f'<text x="{DX + 14}" y="{y}" class="code xs {cls} {until_hold(t)}" xml:space="preserve">'
            f'{s.replace("<", "&lt;").replace(">", "&gt;")}</text>')

# ── Captions ─────────────────────────────────────────────────────────────────
fig.text(20, OUT_Y + OUT_H + 26,
         "Pass 1 runs before any output exists, so a typo in a block name never produces a half-rendered page.", "s")
for start, end, msg in [
    (0, 5.0, "Pass 1: the layout registers its slots, and every #content block in the child is checked against them …"),
    (5.0, 8.0, "Pass 2: the child renders into the shared blocks map; ${ … } runs through the full Notch parser …"),
    (8.0, 11.0, "… then the layout renders, swapping each #content slot for the child's block (or its default)."),
    (11.0, HOLD, "A misspelled block fails in pass 1 with a diagnostic that points at the exact line."),
]:
    fig.text(20, H - 18, msg, f"cap {fig.window(start, end)}")

fig.write()
