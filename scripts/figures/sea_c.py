#!/usr/bin/env python3
"""Animated figure: how sea.c turns `x = a + b * 2;` into a syntax tree.

Writes assets/figures/sea-c.svg.
"""
from html import escape

from common import Figure

W, H = 780, 520
fig = Figure("sea-c", W, H, period=16.0, label=(
    "Diagram of the sea.c project: main.c reads a source file, sea_tokenize splits it into tokens, "
    "and a recursive-descent parser with one function per precedence level builds an "
    "ASSIGN / ADD / MUL syntax tree for x = a + b * 2."))
PERIOD = fig.period
body, track, window, text = fig.body, fig.track, fig.window, fig.text


def appear(start, end):
    """Hidden until start, visible until end."""
    return window(start, end)


# ── Timeline (seconds) ────────────────────────────────────────────────────────
T_READ = 0.3       # main.c reads the file
T_TOK = 1.4        # tokenizer starts emitting chips
T_TOK_STEP = 0.18
T_PARSE = 3.2      # parser starts
STEP = 0.38        # one call down the precedence ladder
T_HOLD = 15.0      # whole tree visible until here, then reset

# Parser call order for `x = a + b * 2`, with what each step produces.
# (ladder row, node created or None, token consumed or None)
CALLS = [
    ("stmt", None, None),
    ("expr", None, None), ("equality", None, None), ("ordinal", None, None),
    ("additive", None, None), ("term", None, None), ("unary", None, None),
    ("primary", "x", 0),
    ("expr", "=", 1),
    ("equality", None, None), ("ordinal", None, None), ("additive", None, None),
    ("term", None, None), ("unary", None, None),
    ("primary", "a", 2),
    ("additive", "+", 3),
    ("term", None, None), ("unary", None, None),
    ("primary", "b", 4),
    ("term", "*", 5),
    ("unary", None, None),
    ("primary", "2", 6),
    ("stmt", None, 7),
]
call_time = [T_PARSE + i * STEP for i in range(len(CALLS))]
T_DONE = call_time[-1] + STEP
assert T_DONE < T_HOLD - 1.5, "timeline overruns the loop"

# ── Card and header ───────────────────────────────────────────────────────────
fig.header("sea.c — from source line to syntax tree", "A small C-like teaching language: tokenize up front, then recursive descent with one function per precedence level.")

# ── Source line and token chips ───────────────────────────────────────────────
SRC_Y = 78
body.append(f'<rect class="box" x="20" y="{SRC_Y}" width="146" height="34" rx="6"/>')
text(32, SRC_Y + 22, "x = a + b * 2;", "code")
text(20, SRC_Y + 50, "main.sea", "s")

body.append(f'<path class="edge" d="M172 {SRC_Y + 17} H262" marker-end="url(#arr)"/>')
text(217, SRC_Y + 10, "sea_tokenize", "s", "middle")

TOKENS = ["x", "=", "a", "+", "b", "*", "2", ";"]
CHIP_X0, CHIP_W, CHIP_GAP = 272, 30, 6
chip_x = []
for i, tok in enumerate(TOKENS):
    x = CHIP_X0 + i * (CHIP_W + CHIP_GAP)
    chip_x.append(x)
    shown = T_TOK + i * T_TOK_STEP
    consumed = next(call_time[j] for j, c in enumerate(CALLS) if c[2] == i)
    cls = track([(0, 0), (shown, 1), (consumed, 0.3), (T_HOLD, 0), (PERIOD, 0)])
    body.append(f'<g class="{cls}"><rect class="chip" x="{x}" y="{SRC_Y + 3}" width="{CHIP_W}" height="28" rx="5"/>'
                f'<text x="{x + CHIP_W / 2}" y="{SRC_Y + 22}" class="code" text-anchor="middle">{escape(tok)}</text></g>')
text(CHIP_X0, SRC_Y + 50, "sea_tokens — every token produced before parsing starts", "s")

# ── File tree ────────────────────────────────────────────────────────────────
TREE_Y = 168
text(20, TREE_Y, "PROJECT", "lbl")
FILES = [
    ("main.c", "CLI: tokenize, repl", [(T_READ, T_TOK)]),
    ("util.c/h", "readFile, streq, repl loop", [(T_READ, T_TOK)]),
    ("sea.c", "tokenizer + parser, 1.6k lines", [(T_TOK, T_DONE)]),
    ("sea.h", "token, AST + error types", [(call_time[7], T_DONE)]),
    ("vec.h", "generic vector (vendored)", [(T_TOK, T_DONE)]),
    ("parsing.md", "design notes", []),
    ("tests/expr", "sample programs", []),
]
for i, (name, note, spans) in enumerate(FILES):
    y = TREE_Y + 18 + i * 40
    for start, end in spans:
        body.append(f'<rect class="hl {window(start, end)}" x="14" y="{y - 2}" width="226" height="36" rx="5"/>')
    branch = "└" if i == len(FILES) - 1 else "├"
    text(22, y + 14, f"{branch} {name}", "code")
    text(36, y + 29, note, "s")

# ── Precedence ladder ─────────────────────────────────────────────────────────
LAD_X, LAD_Y, ROW = 262, 168, 28
text(LAD_X, LAD_Y, "PARSER  (each level calls the one below)", "lbl")
LADDER = [
    ("program", "decl*"),
    ("decl", "extern · func · global"),
    ("stmt", "block if for while var"),
    ("expr", "="),
    ("equality", "== !="),
    ("ordinal", "< > <= >="),
    ("additive", "+ -"),
    ("term", "* / %"),
    ("unary", "! -"),
    ("primary", "int · name · call"),
]
row_y = {}
for i, (name, ops) in enumerate(LADDER):
    y = LAD_Y + 14 + i * ROW
    row_y[name] = y
    body.append(f'<rect class="rung" x="{LAD_X}" y="{y}" width="236" height="{ROW - 4}" rx="4"/>')
for t, (row, _node, _tok) in zip(call_time, CALLS):
    y = row_y[row]
    body.append(f'<rect class="hl {window(t, t + STEP)}" x="{LAD_X}" y="{y}" width="236" height="{ROW - 4}" rx="4"/>')
for name, ops in LADDER:
    y = row_y[name]
    text(LAD_X + 8, y + 16, f"sea_parse_{name}", "code sm")
    text(LAD_X + 228, y + 16, ops, "s", "end")

# ── Syntax tree ──────────────────────────────────────────────────────────────
TX = 520
text(TX, LAD_Y, "AST  (sea_expr nodes)", "lbl")
NODES = {
    "=": (600, 222, "ASSIGN"),
    "x": (546, 290, "SYM x"),
    "+": (656, 290, "ADD"),
    "a": (606, 358, "SYM a"),
    "*": (704, 358, "MUL"),
    "b": (662, 426, "SYM b"),
    "2": (726, 426, "INT 2"),
}
EDGES = [("=", "x"), ("=", "+"), ("+", "a"), ("+", "*"), ("*", "b"), ("*", "2")]
node_time = {c[1]: t for t, c in zip(call_time, CALLS) if c[1]}
for parent, child in EDGES:
    (px, py, _), (cx, cy, _) = NODES[parent], NODES[child]
    t = max(node_time[parent], node_time[child])
    body.append(f'<path class="edge {appear(t, T_HOLD)}" d="M{px} {py + 13} L{cx} {cy - 13}"/>')
for key, (x, y, label) in NODES.items():
    w = 14 + len(label) * 7.4
    cls = appear(node_time[key], T_HOLD)
    body.append(f'<g class="{cls}"><rect class="node" x="{x - w / 2:.1f}" y="{y - 13}" width="{w:.1f}" height="26" rx="13"/>'
                f'<text x="{x}" y="{y + 4.5}" class="code sm" text-anchor="middle">{escape(label)}</text></g>')

# ── Phase captions ───────────────────────────────────────────────────────────
CAP_Y = H - 22
for start, end, msg in [
    (0, T_TOK, "main.c reads the file with util.c's readFile …"),
    (T_TOK, T_PARSE, "… sea_tokenize splits it into tokens up front, so the parser never sees whitespace …"),
    (T_PARSE, T_DONE, "… and the parser walks down the precedence ladder, building a node each time it consumes a token."),
    (T_DONE, T_HOLD, "Errors become nodes too, so one bad token never stops the parse."),
]:
    text(20, CAP_Y, msg, f"cap {window(start, end)}")

fig.write()
