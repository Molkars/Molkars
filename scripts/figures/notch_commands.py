#!/usr/bin/env python3
"""Animated figure: three Sunny (Notch template) commands — fragment, helper, require.

Writes assets/figures/notch-commands.svg. Three scenes cycle in the same frame;
every template, output, and diagnostic was produced by rendering through Notch.
"""
from common import Figure

W, H = 780, 480
SCENE = 7.0
fig = Figure("notch-commands", W, H, period=3 * SCENE, label=(
    "Diagram of three Sunny template commands. #fragment: rendering todos.html#list returns only the "
    "list, for htmx partial updates. #helper: a Java class's public fields become template variables. "
    "#require: declares typed inputs, failing with 'missing required symbol' or 'not assignable' "
    "diagnostics that point at the line."))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def scene_window(i, start=0.0, end=None):
    """Visible inside scene i from `start` seconds into it until `end` (default: scene end)."""
    s0 = i * SCENE
    return fig.window(s0 + start, s0 + (SCENE - 0.3 if end is None else end))


fig.header("Sunny — a few template commands I like",
           "Sunny is Notch's template engine. Each scene below is real input and output.")

# ── Tabs ─────────────────────────────────────────────────────────────────────
TABS = [("#fragment", "render part of a page"), ("#helper", "Java fields as variables"),
        ("#require", "typed template inputs")]
TAB_W = (W - 40 - 16) / 3
for i, (name, sub) in enumerate(TABS):
    x = 20 + i * (TAB_W + 8)
    fig.add(f'<rect class="chip" x="{x:.1f}" y="70" width="{TAB_W:.1f}" height="36" rx="6"/>')
    fig.add(f'<rect class="hl {scene_window(i, 0, SCENE)}" x="{x:.1f}" y="70" width="{TAB_W:.1f}" height="36" rx="6"/>')
    fig.text(x + 12, 86, name, "code sm b")
    fig.text(x + 12, 100, sub, "s")

PANEL_Y, PANEL_H = 136, 274
LX, LW = 20, 372
RX, RW = 404, 356
fig.add(f'<rect class="box" x="{LX}" y="{PANEL_Y}" width="{LW}" height="{PANEL_H}" rx="6"/>')
fig.add(f'<rect class="term" x="{RX}" y="{PANEL_Y}" width="{RW}" height="{PANEL_H}" rx="6"/>')
LINE_H = 21


def source(scene, filename, lines, top=PANEL_Y, highlights=(), start=0.0):
    """Template lines in the left panel. highlights: (first line, last line, t0, t1)."""
    fig.add(f'<text x="{LX}" y="{top - 8}" class="lbl {scene_window(scene)}">{esc(filename)}</text>')
    for first, last, t0, t1 in highlights:
        y = top + 8 + (first - 1) * LINE_H
        fig.add(f'<rect class="hl {scene_window(scene, t0, t1)}" x="{LX + 4}" y="{y}" width="{LW - 8}" '
                f'height="{(last - first + 1) * LINE_H}" rx="3"/>')
    for n, parts in enumerate(lines, 1):
        spans = "".join(f'<tspan class="{c}">{esc(s)}</tspan>' if c else esc(s) for c, s in parts)
        fig.add(f'<text x="{LX + 10}" y="{top + 8 + (n - 1) * LINE_H + 15}" class="code sm {scene_window(scene, start)}" '
                f'xml:space="preserve"><tspan class="cm">{n:>2} </tspan>{spans}</text>')


def output(scene, label, lines, t0, t1=None, cls="termt", top=None):
    """Lines in the right (terminal) panel."""
    y0 = PANEL_Y if top is None else top
    win = scene_window(scene, t0, t1)
    fig.add(f'<text x="{RX + 14}" y="{y0 + 22}" class="code xs termdim {win}">{esc(label)}</text>')
    for i, (c, s) in enumerate(lines):
        fig.add(f'<text x="{RX + 14}" y="{y0 + 44 + i * 19}" class="code xs {c or cls} {win}" '
                f'xml:space="preserve">{esc(s)}</text>')


fig.css.append(".xs { font-size: 11px; }")
CMD, TAG, STR = "k", "f", "str"
fig.text(RX, PANEL_Y - 8, "OUTPUT", "lbl")

# ── Scene 1: #fragment ───────────────────────────────────────────────────────
TODOS = [
    [(CMD, "#require "), ("", "todos: java.util.List")],
    [(TAG, "<h1>"), ("", "My todos"), (TAG, "</h1>")],
    [(CMD, "#fragment "), ("", "list")],
    [(TAG, "<ul>")],
    [(CMD, "#for "), ("", "t "), (CMD, "in "), ("", "todos")],
    [(TAG, "  <li>"), ("num", "${ t }"), (TAG, "</li>")],
    [(CMD, "#end")],
    [(TAG, "</ul>")],
    [(CMD, "#end")],
    [(TAG, "<footer>"), ("", "…"), (TAG, "</footer>")],
]
source(0, "todos.html", TODOS, highlights=[(3, 9, 3.4, SCENE - 0.3)])
output(0, 'render("todos.html")', [
    ("", "<h1>My todos</h1>"), ("", "<ul>"), ("", "  <li>write README</li>"), ("", "  <li>ship it</li>"),
    ("", "</ul>"), ("", "<footer>…</footer>")], 0.5, 3.2)
output(0, 'render("todos.html#list")', [
    ("", "<ul>"), ("", "  <li>write README</li>"), ("", "  <li>ship it</li>"), ("", "</ul>")], 3.4)
fig.add(f'<text x="{RX + 14}" y="{PANEL_Y + PANEL_H - 16}" class="s termdim {scene_window(0, 4.0)}">'
        f'one template, and htmx can swap in just the list</text>')

# ── Scene 2: #helper ─────────────────────────────────────────────────────────
PAGE = [
    [(CMD, "#helper "), ("", "app.SiteHelper")],
    [(TAG, "<title>"), ("num", "${ siteName }"), (TAG, "</title>")],
    [(CMD, "#for "), ("", "item "), (CMD, "in "), ("", "nav")],
    [(TAG, '<a href="/'), ("num", "${ item }"), (TAG, '">'), ("num", "${ item }"), (TAG, "</a>")],
    [(CMD, "#end")],
    [(TAG, "<small>"), ("", "© "), ("num", "${ year }"), (TAG, "</small>")],
]
source(1, "page.html", PAGE, highlights=[(1, 1, 0.4, 1.6)])
JAVA_TOP = PANEL_Y + 8 + len(PAGE) * LINE_H + 22
fig.add(f'<text x="{LX + 10}" y="{JAVA_TOP}" class="lbl {scene_window(1)}">app/SiteHelper.java</text>')
JAVA = [
    [(CMD, "public class "), ("", "SiteHelper {")],
    [(CMD, "  public final "), ("", 'String siteName = '), (STR, '"My App"'), ("", ";")],
    [(CMD, "  public final "), ("", 'List&lt;String&gt; nav = List.of(…);'.replace("&lt;", "<").replace("&gt;", ">"))],
    [(CMD, "  public final "), ("", "int year = "), ("num", "2026"), ("", ";")],
    [("", "}")],
]
fig.add(f'<rect class="hl {scene_window(1, 1.6, 3.2)}" x="{LX + 4}" y="{JAVA_TOP + 8 + LINE_H - 4}" width="{LW - 8}" '
        f'height="{3 * LINE_H}" rx="3"/>')
for i, parts in enumerate(JAVA):
    spans = "".join(f'<tspan class="{c}">{esc(s)}</tspan>' if c else esc(s) for c, s in parts)
    fig.add(f'<text x="{LX + 10}" y="{JAVA_TOP + 8 + i * LINE_H + 10}" class="code xs {scene_window(1)}" '
            f'xml:space="preserve">{spans}</text>')
output(1, 'render("page.html")', [
    ("", "<title>My App</title>"), ("", '<a href="/home">home</a>'), ("", '<a href="/docs">docs</a>'),
    ("", '<a href="/blog">blog</a>'), ("", "<small>© 2026</small>")], 2.4)
fig.add(f'<text x="{RX + 14}" y="{PANEL_Y + PANEL_H - 16}" class="s termdim {scene_window(1, 3.2)}">'
        f'public fields resolve like variables, no wiring code</text>')

# ── Scene 3: #require ────────────────────────────────────────────────────────
source(2, "todos.html", TODOS[:2], highlights=[(1, 1, 0.4, SCENE - 0.3)])
fig.add(f'<text x="{LX + 10}" y="{PANEL_Y + 80}" class="s {scene_window(2, 0.4)}">'
        f'declares what the template needs, with a Java type,</text>')
fig.add(f'<text x="{LX + 10}" y="{PANEL_Y + 96}" class="s {scene_window(2, 0.4)}">'
        f'and fails with a diagnostic that points at the line.</text>')
DIAG_A = [
    ("", "   --> todos.html:1:10"), ("", "    |"), ("", "  1 | #require todos: java.util.List"),
    ("termerr", "    |          ^^^^^"),
    ("termerr", 'note: missing required symbol "todos"'),
    ("termerr", "      (expected java.util.List)"),
]
output(2, 'render("todos.html")   // no todos passed', DIAG_A, 0.8, 3.8)
DIAG_B = [
    ("", "   --> todos.html:1:10"), ("", "    |"), ("", "  1 | #require todos: java.util.List"),
    ("termerr", "    |          ^^^^^"),
    ("termerr", "note: java.lang.String is not assignable"),
    ("termerr", "      to java.util.List"),
]
output(2, 'render("todos.html", todos: "oops")', DIAG_B, 3.9)

# ── Caption ──────────────────────────────────────────────────────────────────
for i, msg in enumerate([
    "#fragment names a region, so a request for todos.html#list renders only that region.",
    "#helper points a template at a Java class; its public fields become variables.",
    "#require turns a template's inputs into a typed contract, with diagnostics that point at the line.",
]):
    fig.text(20, H - 22, msg, f"cap {scene_window(i, 0, SCENE)}")

fig.write()
