#!/usr/bin/env python3
"""Animated figure: everyday Notch syntax.

Writes assets/figures/notch-syntax.svg. Every result shown was produced by
running the line through Notch (local main, including `for i < n`).
"""
from common import Figure

W, H = 780, 656
fig = Figure("notch-syntax", W, H, period=18.0, label=(
    "Diagram of Notch syntax with real results. Strings: 'single', \"double\", and quote-free :terse. "
    "Maps: {:apples -> 3, :pears -> 5} read with m.apples or m[:pears]. Loops: for i < 4 counts 0 "
    "to 3, printing 0 1 4 9. Missing values: an unknown variable is an error, foo?.bar.baz coalesces "
    "to undefined, ?: supplies a fallback, and a misspelled method call errors with a suggestion."))
HOLD = 17.2


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


fig.header("Notch — small syntax, strict where it matters",
           "Syntax I worked on in Notch, MSU's scripting language. Every result below is from a real run.")

# Each group: (title, tagline, rows); each row: (code runs, result, result class, note)
OK, ERR = "", "badt"
GROUPS = [
    ("STRINGS", "three ways to write one", [
        ([("str", "'single'")], "single", OK, None),
        ([("str", '"double"')], "double", OK, None),
        ([("str", ":terse")], "terse", OK, "no quotes: ends at a space or , ) ] }"),
    ]),
    ("MAPS", "terse keys, property-style reads", [
        ([("", "m = {"), ("str", ":apples"), ("", " -> "), ("num", "3"), ("", ", "), ("str", ":pears"),
          ("", " -> "), ("num", "5"), ("", "}")], None, OK, None),
        ([("", "m.apples")], "3", OK, None),
        ([("", "m["), ("str", ":pears"), ("", "]")], "5", OK, None),
    ]),
    ("LOOPS", "count up without a range", [
        ([("k", "for "), ("", "i < "), ("num", "4"), ("", " "), ("f", "print"), ("", "(i * i) "), ("k", "end")],
         "0  1  4  9", OK, "i runs from 0 while i < n"),
    ]),
    ("MISSING VALUES", "variables and calls are strict, property reads coalesce", [
        ([("", "foo")], 'unknown variable "foo"', ERR, "a typo'd variable is an error …"),
        ([("", "foo?.bar.baz "), ("k", "is undefined")], "true", OK, "… unless you opt in with ?"),
        ([("", "foo?.bar.baz "), ("k", "?:"), ("", " "), ("str", ":nope")], "nope", OK, "?: turns <undefined> into a value"),
        ([("str", "'hello'"), ("", "."), ("f", "lenght"), ("", "()")], "no method 'lenght' on String", ERR,
         "Did you mean 'length'?"),
    ]),
]

PANEL_Y = 76
ROW_H, GROUP_GAP, HEAD_H = 34, 10, 26
OUT_X = 452
rows_total = sum(len(g[2]) for g in GROUPS)
panel_h = rows_total * ROW_H + len(GROUPS) * (HEAD_H + GROUP_GAP) + 8
fig.add(f'<rect class="box" x="20" y="{PANEL_Y}" width="{W - 40}" height="{panel_h}" rx="6"/>')

t = 0.4
y = PANEL_Y + 10
group_spans = []
for gi, (title, tagline, rows) in enumerate(GROUPS):
    g_start = t
    fig.add(f'<text x="34" y="{y + 17}" class="lbl">{title}</text>'
            f'<text x="{34 + len(title) * 7.6 + 10:.0f}" y="{y + 17}" class="s">{esc(tagline)}</text>')
    y += HEAD_H
    for parts, result, rcls, note in rows:
        nxt = t + (1.5 if rcls == ERR or note else 1.1)
        fig.add(f'<rect class="hl {fig.window(t, nxt)}" x="26" y="{y}" width="{W - 52}" height="{ROW_H - 4}" rx="4"/>')
        if rcls == ERR:
            fig.add(f'<rect class="bad {fig.window(t + 0.45, HOLD)}" x="{OUT_X - 6}" y="{y + 2}" '
                    f'width="{W - 26 - OUT_X}" height="{ROW_H - 8}" rx="4" style="stroke-opacity:.4"/>')
        spans = "".join(f'<tspan class="{c}">{esc(s)}</tspan>' if c else esc(s) for c, s in parts)
        fig.add(f'<text x="34" y="{y + 20}" class="code sm {fig.window(t, HOLD)}" xml:space="preserve">'
                f'<tspan class="cm">&gt; </tspan>{spans}</text>')
        if result:
            mark = "✗ " if rcls == ERR else ""
            ry = y + (14 if note else 20)
            fig.add(f'<text x="{OUT_X}" y="{ry}" class="code sm b {rcls} {fig.window(t + 0.45, HOLD)}" '
                    f'xml:space="preserve">{esc(mark + result)}</text>')
        if note:
            fig.add(f'<text x="{OUT_X}" y="{y + (27 if result else 20)}" class="s {fig.window(t + 0.45, HOLD)}">'
                    f'{esc(note)}</text>')
        y += ROW_H
        t = nxt
    group_spans.append((g_start, t))
    y += GROUP_GAP
T_END = t
assert T_END < HOLD - 2, "timeline overruns the loop"
fig.add(f'<path class="edge" d="M{OUT_X - 14} {PANEL_Y + 10} V{PANEL_Y + panel_h - 10}" style="stroke-width:1"/>')

# ── Captions ─────────────────────────────────────────────────────────────────
CAPS = [
    "Strings come in three flavours; terse ones are perfect for keys and names …",
    "… which makes map literals read cleanly, and keys read like properties …",
    "… for i < n is the loop you reach for most, without building a range …",
    "… and missing values fail loudly unless you opt in, with a suggestion when you misspell a method.",
]
for (start, end), msg in zip(group_spans, CAPS):
    fig.text(20, H - 18, msg, f"cap {fig.window(start, end if msg is not CAPS[-1] else HOLD)}")

fig.write()
