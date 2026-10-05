#!/usr/bin/env python3
"""Animated figure: how flip's parser reads one line of the paging simulator.

Writes assets/figures/flip-parse.svg. The tokens and tree are what
Flibbity.parse_program produces for this line of admit-job.
"""
from html import escape

from common import Figure

W, H = 780, 556
fig = Figure("flip-parse", W, H, period=17.0, label=(
    "Diagram of flip's parser on pages do-be job-size divided-by s' page-size $'s ceil. "
    "The tokenizer splits on whitespace only, so s' and $'s stay whole words. Recursive descent "
    "walks one function per precedence level, from rbind down to primary, and builds a tree: "
    "do-be pages, then ACCESS ceil over divided-by, whose operands are job-size and s' page-size. "
    "Because $'s binds last, ceil applies to the whole quotient."))
PERIOD = fig.period
text, window, track = fig.text, fig.window, fig.track

# ── Timeline (seconds) ────────────────────────────────────────────────────────
T_READ = 0.3
T_TOK = 1.3
T_TOK_STEP = 0.18
T_PARSE = 3.0
STEP = 0.42
T_HOLD = 16.0

# Parser call order: (ladder row, node created or None, token consumed or None)
CALLS = [
    ("stmt", None, 0),
    ("stmt", "assign", 1),
    ("rbind", None, None), ("either", None, None), ("props", None, None), ("ordinal", None, None),
    ("additive", None, None), ("factor", None, None), ("use", None, None),
    ("primary", "job-size", 2),
    ("factor", "div", 3),
    ("use", None, None),
    ("primary", "s'", 4),
    ("use", "page-size", 5),
    ("rbind", "ceil", 6),
    ("rbind", None, 7),
]
call_time = [T_PARSE + i * STEP for i in range(len(CALLS))]
T_DONE = call_time[-1] + STEP
assert T_DONE < T_HOLD - 4, "timeline overruns the loop"

fig.header("flip — reading a line that is mostly words",
           "Flibbity tokenizes on whitespace alone, then parses by recursive descent with one function per precedence level.")

# ── Source line and token chips ───────────────────────────────────────────────
SRC = "pages do-be job-size divided-by s' page-size $'s ceil"
SRC_Y = 76
fig.add(f'<rect class="box" x="20" y="{SRC_Y}" width="{len(SRC) * 7.85 + 24:.0f}" height="32" rx="6"/>')
fig.runs(32, SRC_Y + 21, [("", "pages "), ("k", "do-be"), ("", " job-size "), ("k", "divided-by"),
                          ("", " s"), ("f", "'"), ("", " page-size "), ("f", "$'s"), ("", " ceil")])
text(W - 20, SRC_Y + 21, "admit-job, dillon-shaffer-1.flip", "s", "end")

CHIP_Y = 134
fig.arrow(f"M32 {SRC_Y + 34} V{CHIP_Y - 4}")
text(42, SRC_Y + 48, "Flibbity._split", "s")

TOKENS = SRC.split()
chip_x, x = [], 20
for i, tok in enumerate(TOKENS):
    w = len(tok) * 7.8 + 16
    chip_x.append((x, w))
    shown = T_TOK + i * T_TOK_STEP
    consumed = next(call_time[j] for j, c in enumerate(CALLS) if c[2] == i)
    cls = track([(0, 0), (shown, 1), (consumed, 0.3), (T_HOLD, 0), (PERIOD, 0)])
    fig.add(f'<g class="{cls}"><rect class="chip" x="{x:.1f}" y="{CHIP_Y}" width="{w:.1f}" height="28" rx="5"/>'
            f'<text x="{x + w / 2:.1f}" y="{CHIP_Y + 19}" class="code" text-anchor="middle">{escape(tok)}</text></g>')
    x += w + 6
text(x + 8, CHIP_Y + 19, "← 8 tokens, no lexer rules", "s")

# ── What's in the file ────────────────────────────────────────────────────────
FILE_Y = 210
text(20, FILE_Y, "DILLON-SHAFFER-1.FLIP", "lbl")
SECTIONS = [
    ("program = \"\"\"…\"\"\"", "the simulator, ~490 lines of flip", [(T_READ, T_TOK)]),
    ("keywords", "do-be, let's, fahhh!, waduhek …", []),
    ("Flibbity._split", "the whole tokenizer, 30 lines", [(T_TOK, T_PARSE)]),
    ("Flibbity._parse_*", "recursive descent + recovery", [(T_PARSE, T_DONE)]),
    ("Expr · Stmt · Decl", "AST nodes that eval themselves", [(call_time[1], T_DONE)]),
    ("Runtime", "scopes, variables, const checks", [(T_DONE + 0.4, T_DONE + 3.6)]),
    ("dump_ast", "writes ast.html to debug with", []),
]
for i, (name, note, spans) in enumerate(SECTIONS):
    y = FILE_Y + 18 + i * 40
    for start, end in spans:
        fig.add(f'<rect class="hl {window(start, end)}" x="14" y="{y - 2}" width="226" height="36" rx="5"/>')
    branch = "└" if i == len(SECTIONS) - 1 else "├"
    text(22, y + 14, f"{branch} {name}", "code sm")
    text(36, y + 29, note, "s")

# ── Precedence ladder ─────────────────────────────────────────────────────────
LAD_X, LAD_Y, ROW = 262, 210, 28
text(LAD_X, LAD_Y, "PARSER  (each level calls the one below)", "lbl")
LADDER = [
    ("stmt", "_parse_basic_stmt", "x y do-be expr"),
    ("rbind", "_rbind", "$'s prop"),
    ("either", "_boolean_or", "either … or …"),
    ("props", "_props", "is · starts-with · is-empty"),
    ("ordinal", "_ordinal", "greater-than …"),
    ("additive", "_additive", "plus · minus"),
    ("factor", "_factor", "times · divided-by"),
    ("use", "_use", "x's prop · 's result"),
    ("primary", "_primary", "word · 42 · :sym · String"),
]
LAD_W = 228
row_y = {}
for i, (key, _fn, _ops) in enumerate(LADDER):
    y = LAD_Y + 14 + i * ROW
    row_y[key] = y
    fig.add(f'<rect class="rung" x="{LAD_X}" y="{y}" width="{LAD_W}" height="{ROW - 4}" rx="4"/>')
for t, (row, _node, _tok) in zip(call_time, CALLS):
    fig.add(f'<rect class="hl {window(t, t + STEP)}" x="{LAD_X}" y="{row_y[row]}" width="{LAD_W}" height="{ROW - 4}" rx="4"/>')
for key, fn, ops in LADDER:
    y = row_y[key]
    text(LAD_X + 8, y + 16, fn, "code sm")
    text(LAD_X + LAD_W - 8, y + 16, ops, "s", "end")

# ── Syntax tree ──────────────────────────────────────────────────────────────
TX = 506
text(TX, LAD_Y, "AST", "lbl")
NODES = {
    "assign": (632, 238, "do-be pages"),
    "ceil": (632, 296, "ACCESS ceil"),
    "div": (632, 354, "divided-by"),
    "job-size": (566, 412, "IDENT job-size"),
    "page-size": (694, 412, "ACCESS page-size"),
    "s'": (694, 470, "IDENT s'"),
}
EDGES = [("assign", "ceil"), ("ceil", "div"), ("div", "job-size"), ("div", "page-size"), ("page-size", "s'")]
node_time = {c[1]: t for t, c in zip(call_time, CALLS) if c[1]}
for parent, child in EDGES:
    (px, py, _), (cx, cy, _) = NODES[parent], NODES[child]
    t = max(node_time[parent], node_time[child])
    fig.add(f'<path class="edge {window(t, T_HOLD)}" d="M{px} {py + 13} L{cx} {cy - 13}"/>')
for key, (x, y, label) in NODES.items():
    w = 16 + len(label) * 6.9
    fig.add(f'<g class="{window(node_time[key], T_HOLD)}"><rect class="node" x="{x - w / 2:.1f}" y="{y - 13}" width="{w:.1f}" height="26" rx="13"/>'
            f'<text x="{x}" y="{y + 4.5}" class="code sm" text-anchor="middle">{escape(label)}</text></g>')
# $'s binds last: bracket the whole quotient it applies to
fig.add(f'<rect class="hl {window(T_DONE, T_DONE + 3.6)}" x="503" y="332" width="257" height="164" rx="10"/>')

# ── Phase captions ───────────────────────────────────────────────────────────
CAP_Y = H - 22
for start, end, parts in [
    (0, T_TOK, [("", "admit-job works out how many pages a job needs …")]),
    (T_TOK, T_PARSE, [("", "… "), ("code", "_split"), ("", " cuts on whitespace alone, so "), ("code", "s'"),
                      ("", " and "), ("code", "$'s"), ("", " stay glued to their words …")]),
    (T_PARSE, T_DONE, [("", "… and the parser walks down the ladder, one function per level, building nodes as it goes.")]),
    (T_DONE, T_DONE + 3.6, [("code", "$'s"), ("", " binds last, so "), ("code", "ceil"),
                            ("", " applies to the whole quotient: ⌈job-size ÷ page-size⌉.")]),
    (T_DONE + 3.6, T_HOLD, [("", "A parse error skips to "), ("code", "end-<name>"),
                            ("", ", so one run reports every broken function.")]),
]:
    fig.runs(20, CAP_Y, parts, f"cap {window(start, end)}")

fig.write()
