#!/usr/bin/env python3
"""Animated figure: compiling Sea to the Little Man Stack Machine, then running it.

Writes assets/figures/sea-lmsm.svg. ASM is the verbatim output of the Sea
compiler (lmsm/src/sea.c in msu/csci-366-spring2025) for SOURCE. The run trace
is computed by the small interpreter below, which follows the LMSM README's
instruction semantics.
"""
from common import Figure

SOURCE = """int main() {
    for (int i = 0; i < 4; i = i + 1) {
        putn(i * i);
    }
    return 0;
}"""

ASM = """CALL main
HLT
main SPSUB 0
SPUSHI 0
SSTA 0
$for.cond0 SLDA 0
SPUSHI 4
SCMPLT
SPOP
BRZ $for.end0
SLDA 0
SLDA 1
SMUL
SPOP
OUT
SLDA 0
SPUSHI 1
SADD
SSTA 0
BRA $for.cond0
$for.end0 ADD $0
SPUSHI 0
BRA $ret.main
$ret.main SPOP
SPADD 0
RET
$0 DAT 0"""

# Which source fragment each run of assembly lines came from: (first asm line, last, label,
# source line, start col, end col) — columns index into SOURCE's lines.
BLOCKS = [
    (0, 1, "call main, halt", 1, 0, 12),
    (2, 2, "frame: 1 local", 1, 0, 12),
    (3, 4, "int i = 0", 2, 9, 18),
    (5, 9, "i < 4 ? else exit", 2, 20, 25),
    (10, 14, "putn(i * i)", 3, 8, 20),
    (15, 18, "i = i + 1", 2, 27, 36),
    (19, 19, "loop", 2, 4, 7),
    (20, 22, "return 0", 5, 4, 13),
    (23, 25, "epilogue", 6, 0, 1),
    (26, 26, "constant pool", 5, 11, 12),
]


# ── Interpreter for the instructions the compiler emitted ────────────────────
def parse(asm):
    lines, labels = [], {}
    for i, raw in enumerate(asm.splitlines()):
        parts = raw.split()
        if parts[0] not in OPS:
            labels[parts[0]] = i
            parts = parts[1:]
        lines.append((parts[0], parts[1] if len(parts) > 1 else None))
    return lines, labels


OPS = {"CALL", "HLT", "SPSUB", "SPADD", "SPUSHI", "SSTA", "SLDA", "SCMPLT", "SPOP", "BRZ", "BRA",
       "SMUL", "SADD", "OUT", "ADD", "RET", "DAT"}


def run(asm):
    lines, labels = parse(asm)
    memory = {label: int(arg) for label, (op, arg) in
              ((lab, lines[i]) for lab, i in labels.items()) if op == "DAT"}
    acc, stack, out, pc, ret = 0, [], [], 0, None
    trace = []
    while True:
        op, arg = lines[pc]
        trace.append((pc, acc, list(stack), list(out)))
        nxt = pc + 1
        if op == "CALL":
            ret, nxt = nxt, labels[arg]
        elif op == "HLT":
            break
        elif op == "SPSUB":
            stack += [0] * (int(arg) + 1)
        elif op == "SPADD":
            del stack[len(stack) - (int(arg) + 1):]
        elif op == "SPUSHI":
            stack.append(int(arg))
        elif op == "SSTA":
            v = stack.pop()
            stack[-1 - int(arg)] = v
        elif op == "SLDA":
            stack.append(stack[-1 - int(arg)])
        elif op in ("SCMPLT", "SMUL", "SADD"):
            top, second = stack.pop(), stack.pop()
            stack.append({"SCMPLT": int(second < top), "SMUL": second * top, "SADD": second + top}[op])
        elif op == "SPOP":
            acc = stack.pop()
        elif op == "BRZ":
            if acc == 0:
                nxt = labels[arg]
        elif op == "BRA":
            nxt = labels[arg]
        elif op == "OUT":
            out.append(acc)
        elif op == "ADD":
            acc += memory[arg]
        elif op == "RET":
            nxt = ret
        pc = nxt
    trace.append((pc, acc, list(stack), list(out)))
    return trace


TRACE = run(ASM)
assert TRACE[-1][3] == [0, 1, 4, 9], TRACE[-1][3]

# ── Timeline ─────────────────────────────────────────────────────────────────
T_COMPILE, BLOCK_STEP = 0.4, 0.45
T_RUN = T_COMPILE + len(BLOCKS) * BLOCK_STEP + 0.8
SLOW_STEPS, SLOW, FAST = 19, 0.38, 0.11
step_t = []
t = T_RUN
for i in range(len(TRACE)):
    step_t.append(t)
    t += SLOW if i < SLOW_STEPS else FAST
T_DONE = t
HOLD = T_DONE + 2.4

W, H = 780, 600
fig = Figure("sea-lmsm", W, H, period=round(HOLD + 0.6, 1), label=(
    "Diagram of the Sea compiler targeting the Little Man Stack Machine. A Sea for loop that prints "
    "i * i for i < 4 compiles to 27 lines of LMSM stack assembly, each block linked to the source it "
    "came from; a program counter then steps through the assembly, showing the stack and accumulator, "
    "and the output reads 0 1 4 9."))


def until_hold(t0):
    return fig.window(t0, HOLD)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


fig.header("Sea → Little Man Stack Machine",
           "The compiler I wrote for MSU's systems course, emitting stack-machine assembly for a "
           "100-cell teaching computer.")

# ── Phase indicator ──────────────────────────────────────────────────────────
for i, (label, a, b) in enumerate([("1 · compile: each Sea construct becomes a block of stack code", 0.2, T_RUN),
                                   ("2 · run: step through it on the LMSM", T_RUN, HOLD)]):
    x = 20 + i * 374
    fig.add(f'<rect class="chip" x="{x}" y="70" width="366" height="26" rx="13"/>')
    fig.add(f'<rect class="hl {fig.window(a, b)}" x="{x}" y="70" width="366" height="26" rx="13"/>')
    fig.text(x + 183, 87, label, "sm b", "middle")

# ── Source ───────────────────────────────────────────────────────────────────
TOP = 130
SX, SW = 20, 300
CW = 6.62            # 11px monospace advance
SRC_LH = 22
fig.text(SX, TOP - 8, "SEA  loop.sea", "lbl")
fig.add(f'<rect class="box" x="{SX}" y="{TOP}" width="{SW}" height="{6 * SRC_LH + 20}" rx="6"/>')
src_lines = SOURCE.splitlines()
for bi, (a, b, label, line, c0, c1) in enumerate(BLOCKS):
    ta = T_COMPILE + bi * BLOCK_STEP
    y = TOP + 10 + (line - 1) * SRC_LH
    fig.add(f'<rect class="hl {fig.window(ta, ta + BLOCK_STEP)}" x="{SX + 8 + (c0 + 2) * CW - 2:.1f}" y="{y}" '
            f'width="{(c1 - c0) * CW + 4:.1f}" height="{SRC_LH - 2}" rx="3"/>')
KW = {"int", "for", "return"}
for n, line in enumerate(src_lines, 1):
    y = TOP + 10 + (n - 1) * SRC_LH + 15
    parts, word = [], ""
    for ch in line + " ":
        if ch.isalnum() or ch == "_":
            word += ch
            continue
        if word:
            parts.append(("k" if word in KW else "f" if word in ("putn", "main") else
                          "num" if word.isdigit() else "", word))
            word = ""
        parts.append(("", ch))
    spans = "".join(f'<tspan class="{c}">{esc(s)}</tspan>' if c else esc(s) for c, s in parts)
    fig.add(f'<text x="{SX + 8}" y="{y}" class="code xs" xml:space="preserve"><tspan class="cm">{n} </tspan>{spans}</text>')
fig.css.append(".xs { font-size: 11px; }")

# ── State: accumulator, stack, output ────────────────────────────────────────
STX = SX
STY = TOP + 6 * SRC_LH + 52
STATE_H = len(ASM.splitlines()) * 15.4 + 16 - (STY - TOP)
fig.text(STX, STY - 8, "MACHINE STATE", "lbl")
fig.add(f'<rect class="box" x="{STX}" y="{STY}" width="{SW}" height="{STATE_H:.0f}" rx="6"/>')
VX = STX + 100
ACC_Y, STACK_Y, OUT_Y = STY + 16, STY + 62, STY + 124
fig.text(STX + 14, ACC_Y + 17, "accumulator", "s")
fig.text(STX + 14, STACK_Y + 17, "stack", "s")
fig.text(STX + 14, STACK_Y + 34, "bottom → top", "s")
fig.text(STX + 14, OUT_Y + 17, "output", "s")
SLOT_W, SLOT_H = 40, 26
EXPLAIN = {
    "CALL": "jump to main, remembering where to return",
    "SPSUB": "make room on the stack for local i",
    "SPUSHI": "push a constant",
    "SSTA": "pop, then store into a stack slot (i)",
    "SLDA": "copy a stack slot (i) onto the top",
    "SCMPLT": "pop two, push 1 if second < top",
    "SPOP": "pop the top into the accumulator",
    "BRZ": "leave the loop if the accumulator is 0",
    "SMUL": "pop two, push their product",
    "SADD": "pop two, push their sum",
    "OUT": "print the accumulator",
    "BRA": "jump back to the loop test",
}
asm_ops = [raw.split()[1] if raw.split()[0] not in OPS else raw.split()[0] for raw in ASM.splitlines()]
for i, (pc, acc, stack, out) in enumerate(TRACE):
    t0 = step_t[i]
    t1 = step_t[i + 1] if i + 1 < len(TRACE) else HOLD
    parts = [f'<text x="{VX}" y="{ACC_Y + 18}" class="code sm b">{acc}</text>']
    for j, v in enumerate(stack):
        x = VX + j * (SLOT_W + 6)
        parts.append(f'<rect class="{"node" if j == len(stack) - 1 else "chip"}" x="{x}" y="{STACK_Y}" '
                     f'width="{SLOT_W}" height="{SLOT_H}" rx="5"/>'
                     f'<text x="{x + SLOT_W / 2}" y="{STACK_Y + 17}" class="code sm" text-anchor="middle">{v}</text>')
        if j == 0:
            parts.append(f'<text x="{x + SLOT_W / 2}" y="{STACK_Y + SLOT_H + 14}" class="s" text-anchor="middle">i</text>')
    if not stack:
        parts.append(f'<text x="{VX}" y="{STACK_Y + 17}" class="s">empty</text>')
    if i < SLOW_STEPS and pc < len(asm_ops) and asm_ops[pc] in EXPLAIN:
        parts.append(f'<text x="{STX + 14}" y="{STY + STATE_H - 18:.0f}" class="sm">'
                     f'<tspan class="code k">{asm_ops[pc]}</tspan>  {esc(EXPLAIN[asm_ops[pc]])}</text>')
    fig.add(f'<g class="{fig.window(t0, t1)}">{"".join(parts)}</g>')
# Output tape: each value appears when OUT runs and stays.
seen = 0
for i, (_pc, _acc, _stack, out) in enumerate(TRACE):
    while seen < len(out):
        x = VX + seen * 34
        fig.add(f'<g class="{until_hold(step_t[i])}"><rect class="chip" x="{x}" y="{OUT_Y}" width="28" '
                f'height="26" rx="5"/><text x="{x + 14}" y="{OUT_Y + 17}" class="code sm b ok" '
                f'text-anchor="middle">{out[seen]}</text></g>')
        seen += 1

# ── Assembly ─────────────────────────────────────────────────────────────────
AX, AW = 334, W - 20 - 334
ALH = 15.4
fig.text(AX, TOP - 8, "LMSM ASSEMBLY  (real compiler output)", "lbl")
fig.add(f'<rect class="box" x="{AX}" y="{TOP}" width="{AW}" height="{len(ASM.splitlines()) * ALH + 16}" rx="6"/>')
asm_lines = ASM.splitlines()


def asm_y(i):
    return TOP + 8 + i * ALH


for bi, (a, b, label, *_rest) in enumerate(BLOCKS):
    ta = T_COMPILE + bi * BLOCK_STEP
    y0, y1 = asm_y(a), asm_y(b) + ALH
    fig.add(f'<rect class="hl {fig.window(ta, ta + BLOCK_STEP)}" x="{AX + 4}" y="{y0}" width="{AW - 8}" '
            f'height="{y1 - y0}" rx="3"/>')
    fig.add(f'<g class="{until_hold(ta)}"><path class="edge" d="M{AX + AW - 150} {y0 + 2} h-6 V{y1 - 2} h6" '
            f'style="stroke-width:1"/><text x="{AX + AW - 140}" y="{(y0 + y1) / 2 + 4}" class="s">{esc(label)}</text></g>')
for i, raw in enumerate(asm_lines):
    parts = raw.split()
    block = next(bi for bi, blk in enumerate(BLOCKS) if blk[0] <= i <= blk[1])
    label = parts[0] if parts[0] not in OPS else ""
    rest = parts[1:] if label else parts
    win = until_hold(T_COMPILE + block * BLOCK_STEP)
    fig.add(f'<text x="{AX + 10}" y="{asm_y(i) + 11.5}" class="code xs {win}" xml:space="preserve">'
            f'<tspan class="cm">{i:>2} </tspan><tspan class="f">{esc(label.ljust(11))}</tspan>'
            f'<tspan class="k">{esc(rest[0])}</tspan> {esc(" ".join(rest[1:]))}</text>')
# Program counter
for i, (pc, *_rest) in enumerate(TRACE[:-1]):
    t0 = step_t[i]
    t1 = step_t[i + 1]
    fig.add(f'<rect class="bad {fig.window(t0, t1)}" x="{AX + 4}" y="{asm_y(pc)}" width="{AW - 160}" '
            f'height="{ALH}" rx="3" style="fill-opacity:.22"/>')

# ── Captions ─────────────────────────────────────────────────────────────────
for start, end, msg in [
    (0, T_RUN, "Each Sea construct compiles to a small block of stack code; locals live in stack slots."),
    (T_RUN, step_t[SLOW_STEPS], "Running it: SLDA copies i to the top, SCMPLT tests i < 4, SPOP moves the result to the accumulator …"),
    (step_t[SLOW_STEPS], HOLD, "… and every OUT prints i * i, so the tape reads 0 1 4 9."),
]:
    fig.text(20, H - 18, msg, f"cap {fig.window(start, end)}")

fig.write()
