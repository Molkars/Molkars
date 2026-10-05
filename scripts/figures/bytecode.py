#!/usr/bin/env python3
"""Animated figure: the CSCI 468 bytecode generator catching a type error.

Writes assets/figures/bytecode.svg. Shows the pipeline, then a student's
AdditiveExpression.compile() emitting IADD over `1 + "cats"`: the builder's
type stack rejects it, and getSource() points the error at the student's line.
"""
from common import Figure

W, H = 780, 612
fig = Figure("bytecode", W, H, period=15.0, label=(
    "Diagram of a JVM bytecode generator for CatScript. AST nodes call ByteCodeGenerator, whose "
    "BytecodeBuilder tracks a stack of types. Compiling 1 + \"cats\" with iAdd pushes int and String, "
    "so IADD is rejected with 'String is not assignable to int', and getSource() walks the stack "
    "trace so the error points at the student's AdditiveExpression.java line 104."))
HOLD = 14.2


def until_hold(t):
    return fig.window(t, HOLD)


fig.header("CatScript → JVM bytecode, with a type checker in the loop",
           "A bytecode generator I built for MSU's compilers course: it checks every instruction "
           "before the JVM does.")

# ── Pipeline ─────────────────────────────────────────────────────────────────
fig.text(20, 82, "PIPELINE", "lbl")
STAGES = [
    ("CatScript AST", "node.compile(code)"),
    ("ByteCodeGenerator", "push · iAdd · jumpTo …"),
    ("BytecodeBuilder", "basic blocks + type stack"),
    ("ASM ClassWriter", ".class bytes"),
    ("DynamicClassLoader", "load and run"),
]
BOX_W, BOX_GAP, BOX_Y, BOX_H = 134, 18, 90, 48
box_x = [20 + i * (BOX_W + BOX_GAP) for i in range(len(STAGES))]
# When each stage is "active": (stage index, start, end)
STAGE_ACTIVE = [
    (0, 0.2, 1.0), (0, 1.0, 1.4), (1, 1.4, 1.8), (2, 1.8, 2.4),
    (0, 2.6, 2.8), (1, 2.8, 3.4), (2, 3.4, 4.0),
    (0, 4.2, 4.4), (1, 4.4, 5.0), (2, 5.0, HOLD),
]
for x, (title, sub) in zip(box_x, STAGES):
    fig.add(f'<rect class="box" x="{x}" y="{BOX_Y}" width="{BOX_W}" height="{BOX_H}" rx="6"/>')
for i, start, end in STAGE_ACTIVE:
    fig.add(f'<rect class="hl {fig.window(start, end)}" x="{box_x[i]}" y="{BOX_Y}" width="{BOX_W}" height="{BOX_H}" rx="6"/>')
for x, (title, sub) in zip(box_x, STAGES):
    fig.text(x + BOX_W / 2, BOX_Y + 20, title, "b", "middle")
    fig.text(x + BOX_W / 2, BOX_Y + 36, sub, "s", "middle")
# The exception fires during compile(), so no class is ever built.
mid = (box_x[3] + box_x[4] + BOX_W) / 2
fig.add(f'<text x="{mid}" y="{BOX_Y - 6}" class="sm badt b {until_hold(5.6)}" text-anchor="middle">'
        f'never reached: no .class is built</text>')
for x in box_x[:-1]:
    fig.arrow(f"M{x + BOX_W + 2} {BOX_Y + BOX_H / 2} H{x + BOX_W + BOX_GAP - 2}")
fig.text(20, BOX_Y + BOX_H + 20,
         "Every Instruction declares the types it pops and pushes; the builder checks them the moment each one is emitted.", "s")

# ── Example: student code / emitted instructions / type stack ────────────────
PANEL_Y, PANEL_H = 206, 150
COL1, COL1_W = 20, 366
COL2, COL2_W = 398, 160
COL3, COL3_W = 570, 190
fig.text(COL1, PANEL_Y - 8, 'STUDENT CODE  (compiling 1 + "cats")', "lbl")
fig.text(COL2, PANEL_Y - 8, "EMITTED", "lbl")
fig.text(COL3, PANEL_Y - 8, "TYPE STACK", "lbl")
for x, w in ((COL1, COL1_W), (COL2, COL2_W), (COL3, COL3_W)):
    fig.add(f'<rect class="box" x="{x}" y="{PANEL_Y}" width="{w}" height="{PANEL_H}" rx="6"/>')

LINE_H = 24
CODE = [
    (101, [("k", "public void "), ("f", "compile"), ("", "(ByteCodeGenerator code) {")]),
    (102, [("", "    getLeftHandSide()."), ("f", "compile"), ("", "(code);")]),
    (103, [("", "    getRightHandSide()."), ("f", "compile"), ("", "(code);")]),
    (104, [("", "    code."), ("f", "iAdd"), ("", "();")]),
    (105, [("", "}")]),
]
LINE_ACTIVE = {101: [(0.2, 1.0)], 102: [(1.0, 2.6)], 103: [(2.6, 4.2)], 104: [(4.2, 5.4)]}


def line_y(n):
    return PANEL_Y + 14 + (n - 101) * LINE_H


for n, spans in LINE_ACTIVE.items():
    for start, end in spans:
        fig.add(f'<rect class="hl {fig.window(start, end)}" x="{COL1 + 4}" y="{line_y(n)}" '
                f'width="{COL1_W - 8}" height="{LINE_H - 2}" rx="3"/>')
fig.add(f'<rect class="bad {until_hold(5.4)}" x="{COL1 + 4}" y="{line_y(104)}" width="{COL1_W - 8}" '
        f'height="{LINE_H - 2}" rx="3"/>')
for n, parts in CODE:
    fig.runs(COL1 + 10, line_y(n) + 16, [("cm", f"{n}  ")] + parts, "code sm")
fig.add(f'<text x="{COL1 + COL1_W - 10}" y="{line_y(104) + 16}" class="code sm badt {until_hold(9.2)}" '
        f'text-anchor="end">← reported here</text>')

INSTRS = [
    (1.6, "LDC 1", "→ int"),
    (3.2, 'LDC "cats"', "→ String"),
    (4.8, "IADD", "int, int → int"),
]
for i, (t, op, sig) in enumerate(INSTRS):
    y = PANEL_Y + 14 + i * 40
    fig.add(f'<g class="{until_hold(t)}"><rect class="chip" x="{COL2 + 8}" y="{y}" width="{COL2_W - 16}" height="34" rx="5"/>'
            f'<text x="{COL2 + 18}" y="{y + 15}" class="code sm">{op.replace(chr(34), "&quot;")}</text>'
            f'<text x="{COL2 + 18}" y="{y + 29}" class="s">{sig}</text></g>')
iadd_y = PANEL_Y + 14 + 2 * 40
fig.add(f'<rect class="bad {until_hold(5.6)}" x="{COL2 + 8}" y="{iadd_y}" width="{COL2_W - 16}" height="34" rx="5"/>')
fig.add(f'<text x="{COL2 + COL2_W - 18}" y="{iadd_y + 22}" class="code badt b {until_hold(5.6)}" text-anchor="end">✗</text>')

SLOT_W, SLOT_H = 120, 30
slot_x = COL3 + (COL3_W - SLOT_W) / 2
base_y = PANEL_Y + PANEL_H - 14
fig.add(f'<path class="edge" d="M{slot_x - 10} {base_y} H{slot_x + SLOT_W + 10}"/>')
SLOTS = [(2.0, "int"), (3.6, "String")]
for i, (t, ty) in enumerate(SLOTS):
    y = base_y - (i + 1) * (SLOT_H + 4)
    fig.add(f'<g class="{until_hold(t)}"><rect class="chip" x="{slot_x}" y="{y}" width="{SLOT_W}" height="{SLOT_H}" rx="5"/>'
            f'<text x="{slot_x + SLOT_W / 2}" y="{y + 20}" class="code sm" text-anchor="middle">{ty}</text></g>')
top_y = base_y - 2 * (SLOT_H + 4)
fig.add(f'<rect class="bad {until_hold(5.4)}" x="{slot_x}" y="{top_y}" width="{SLOT_W}" height="{SLOT_H}" rx="5"/>')
fig.add(f'<text x="{slot_x + SLOT_W / 2}" y="{top_y - 12}" class="sm badt b {until_hold(5.4)}" text-anchor="middle">'
        f'IADD expects int</text>')
fig.add(f'<text x="{slot_x + SLOT_W / 2}" y="{top_y - 12}" class="s {fig.window(4.8, 5.4)}" text-anchor="middle">'
        f'checking top of stack…</text>')

# ── Console ──────────────────────────────────────────────────────────────────
CON_Y = 392
fig.text(20, CON_Y - 8, "WHAT THE STUDENT SEES", "lbl")
fig.add(f'<rect class="term" x="20" y="{CON_Y}" width="{W - 40}" height="62" rx="6"/>')
fig.add(f'<text x="34" y="{CON_Y + 24}" class="code sm termerr {until_hold(6.2)}">'
        f'java.lang.IllegalArgumentException: String is not assignable to int</text>')
fig.add(f'<text x="34" y="{CON_Y + 44}" class="code sm termt {until_hold(6.8)}" xml:space="preserve">'
        f'  at: csci468.parser.expressions.AdditiveExpression.compile(AdditiveExpression.java:104)</text>')
fig.add(f'<text x="34" y="{CON_Y + 34}" class="code sm termdim {fig.window(0, 6.2)}">$ ./gradlew test</text>')

# ── getSource(): walking the stack trace ─────────────────────────────────────
GS_Y = 494
fig.text(20, GS_Y - 8, "HOW IT FINDS THAT LINE  —  getSource() walks the live stack trace", "lbl")
FRAMES = [
    ("getStackTrace", None),
    ("ByteCodeGenerator.getSource", "gen"),
    ("ByteCodeGenerator.iAdd", "gen"),
    ("AdditiveExpression.compile:104", "you"),
    ("…", None),
]
CHAR_W, PAD = 6.65, 16
fig.css.append(".xs { font-size: 11px; }")
fx = 20
frame_x = []
for name, _ in FRAMES:
    w = len(name) * CHAR_W + PAD
    frame_x.append((fx, w))
    fx += w + 8
scale = min(1.0, (W - 20 - 20 - 8 * (len(FRAMES) - 1)) / sum(w for _, w in frame_x))
fx = 20
for i, (name, kind) in enumerate(FRAMES):
    w = frame_x[i][1] * scale
    t = 7.6 + i * 0.45
    fig.add(f'<rect class="chip" x="{fx:.1f}" y="{GS_Y}" width="{w:.1f}" height="28" rx="5"/>')
    if kind == "gen":
        fig.add(f'<rect class="hl {until_hold(t)}" x="{fx:.1f}" y="{GS_Y}" width="{w:.1f}" height="28" rx="5"/>')
    elif kind == "you":
        fig.add(f'<rect class="bad {until_hold(t)}" x="{fx:.1f}" y="{GS_Y}" width="{w:.1f}" height="28" rx="5"/>')
    else:
        fig.add(f'<rect class="hl {fig.window(t, t + 0.45)}" x="{fx:.1f}" y="{GS_Y}" width="{w:.1f}" height="28" rx="5"/>')
    fig.text(fx + w / 2, GS_Y + 18.5, name, "code xs", "middle")
    if i < len(FRAMES) - 1:
        fig.arrow(f"M{fx + w + 1:.1f} {GS_Y + 14} H{fx + w + 7:.1f}")
    fx += w + 8
fig.text(20, GS_Y + 46, "Every instruction records the first frame after the last ByteCodeGenerator frame: the caller, "
         "not the library.", "s")
fig.add(f'<text x="20" y="{GS_Y + 62}" class="s {until_hold(9.0)}">'
        f'<tspan class="badt b">red</tspan> = the frame reported in the error · '
        f'<tspan style="fill:#4493f8" class="b">blue</tspan> = generator frames that get skipped</text>')

# ── Captions ─────────────────────────────────────────────────────────────────
for start, end, msg in [
    (0, 4.2, "Each AST node compiles itself by calling the generator; every instruction declares the types it pops and pushes …"),
    (4.2, 6.2, "… so the builder tracks a stack of types. IADD needs two ints but finds a String, so it's rejected …"),
    (6.2, 7.6, "… with an error message a student can act on …"),
    (7.6, HOLD, "… that points at their own line, because getSource() skips every frame inside the generator."),
]:
    fig.text(20, H - 18, msg, f"cap {fig.window(start, end)}")

fig.write()
