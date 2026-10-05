#!/usr/bin/env python3
"""Animated figure: pcode-emulator-rs stepping three x86 instructions of fib(10) as P-code.

Writes assets/figures/pcode-emulator.svg. OPS is Ghidra's Sleigh output for
x86:LE:32 (checked with pypcode, IMARKs dropped) for 0x8049746..0x804974D of
tests/fib/bin. The values come from the small interpreter below; the stack
address follows from the emulator's initial ESP (0xFFFFCBB8) through main's
prologue, `mov [esp], 0xa`, the call, and fib's `push ebp`.
"""
from html import escape

from common import Figure

EBP = 0xFFFFCB94
RAM = {EBP + 8: 10}  # fib's argument n

# (address, x86 as objdump shows it, Sleigh mnemonic, Sleigh body, ops)
# op = (opcode, output, inputs); names starting with $U are unique-space temporaries.
INSNS = [
    (0x8049746, "mov eax, [ebp+0x8]", "MOV", "EAX,dword ptr [EBP + 0x8]", [
        ("IntAdd", "$U6600", ["EBP", 0x8]),
        ("Load", "$U17200", ["$U6600"]),
        ("Copy", "EAX", ["$U17200"]),
    ]),
    (0x8049749, "cmp [ebp+0x8], 0x2", "CMP", "dword ptr [EBP + 0x8],0x2", [
        ("IntAdd", "$U6600", ["EBP", 0x8]),
        ("Load", "$U17200", ["$U6600"]),
        ("Copy", "$U66100", ["$U17200"]),
        ("IntLess", "CF", ["$U66100", 0x2]),
        ("IntSBorrow", "OF", ["$U66100", 0x2]),
        ("IntSub", "$U66300", ["$U66100", 0x2]),
        ("IntSLess", "SF", ["$U66300", 0x0]),
        ("IntEqual", "ZF", ["$U66300", 0x0]),
        ("IntAnd", "$U49800", ["$U66300", 0xFF]),
        ("PopCount", "$U49900", ["$U49800"]),
        ("IntAnd", "$U49a00", ["$U49900", 0x1]),
        ("IntEqual", "PF", ["$U49a00", 0x0]),
    ]),
    (0x804974D, "jge 0x804975f", "JGE", "0x804975f", [
        ("IntEqual", "$U18900", ["OF", "SF"]),
        ("CBranch", None, [0x804975F, "$U18900"]),
    ]),
]
TARGET = (0x804975F, "mov ebx, [ebp-0xc]")

FLAGS = ["CF", "OF", "SF", "ZF", "PF"]
UNIQUES = ["$U6600", "$U17200", "$U66100", "$U66300", "$U49800", "$U49900", "$U49a00", "$U18900"]
SIZE = {"EAX": 4, "EBP": 4, **{f: 1 for f in FLAGS},
        "$U49900": 1, "$U49a00": 1, "$U18900": 1}


# ── Interpreter for the opcodes above, after emulate_one's match arms ────────
def run():
    regs = {"EAX": 0x80EF000, "EBP": EBP}  # EAX holds fib's GOT pointer from the prologue
    steps = []  # (insn index, op index, output name, value, emulator log line)

    def signed(v, size):
        bits = size * 8
        return v - (1 << bits) if v >> (bits - 1) else v

    for n, (addr, _x86, mnem, body, ops) in enumerate(INSNS):
        for i, (opcode, out, ins) in enumerate(ops):
            a, b = [regs[x] if isinstance(x, str) else x for x in ins] + [None] * (2 - len(ins))
            size = SIZE.get(out, 4)
            mask = (1 << size * 8) - 1
            value = {
                "IntAdd": lambda: (a + b) & mask,
                "Load": lambda: RAM[a],
                "Copy": lambda: a,
                "IntLess": lambda: int(a < b),
                "IntSBorrow": lambda: int(not -2**31 <= signed(a, 4) - signed(b, 4) < 2**31),
                "IntSub": lambda: (a - b) & mask,
                "IntSLess": lambda: int(signed(a, 4) < signed(b, 4)),
                "IntEqual": lambda: int(a == b),
                "IntAnd": lambda: a & b,
                "PopCount": lambda: bin(a).count("1"),
                "CBranch": lambda: None,
            }[opcode]()
            head = f"emulating {addr:08X}.{i:02X} {opcode: <20} - ({mnem}) {body}"
            if out is None:
                log = f"  branch to {a:X}" if b else "  fall through"
            else:
                regs[out] = value
                raw = ", ".join(f"{(value >> 8 * k) & 0xFF:X}" for k in range(size))
                name = f"unique:{out[2:]}+{size}" if out.startswith("$U") else out
                log = f"  wrote [{raw}] to {name}"
            steps.append((n, i, out, value, head, log))
    return steps


STEPS = run()

# ── Timeline (seconds) ────────────────────────────────────────────────────────
T_LIFT = 0.3       # pipeline boxes light up one after another
LIFT_STEP = 0.6
T_RUN = 2.8        # first P-code op
STEP = 0.55
step_time = [T_RUN + k * STEP for k in range(len(STEPS))]
T_DONE = step_time[-1] + STEP
T_HOLD = T_DONE + 3.0
fig = Figure("pcode-emulator", 780, 620, period=T_HOLD + 0.8, label=(
    "Animated diagram of pcode-emulator-rs: llvm-readobj reads an i386 ELF, Sleigh lifts its code to "
    "P-code, and the emulator interprets each op over register, unique and ram spaces. Three "
    "instructions of fib(10) run as 17 P-code ops: mov loads n = 10 into EAX, cmp sets five flags "
    "through twelve ops, and jge branches to 0x804975F."))
PERIOD = fig.period
body, track, window, text = fig.body, fig.track, fig.window, fig.text
insn_start = [next(t for t, s in zip(step_time, STEPS) if s[0] == n) for n in range(len(INSNS))]
insn_end = insn_start[1:] + [T_DONE]

fig.header("pcode-emulator-rs — x86 by way of Ghidra's P-code",
           "Sleigh lifts each machine instruction into P-code ops; the emulator interprets those ops over sparse byte spaces.")

# ── Pipeline ─────────────────────────────────────────────────────────────────
PIPE_Y, PIPE_W, PIPE_GAP = 74, 166, 25
PIPE = [
    ("tests/fib/bin", "static i386 ELF"),
    ("llvm-readobj", "sections + symbols as JSON"),
    ("Sleigh (C++ FFI)", ".text → P-code per address"),
    ("Emulator", "emulate_one(pcode)"),
]
for i, (name, note) in enumerate(PIPE):
    x = 20 + i * (PIPE_W + PIPE_GAP)
    body.append(f'<rect class="box" x="{x}" y="{PIPE_Y}" width="{PIPE_W}" height="44" rx="6"/>')
    start = T_LIFT + i * LIFT_STEP
    end = T_HOLD if i == len(PIPE) - 1 else start + LIFT_STEP
    body.append(f'<rect class="hl {window(start, end)}" x="{x}" y="{PIPE_Y}" width="{PIPE_W}" height="44" rx="6"/>')
    text(x + 10, PIPE_Y + 19, name, "code sm b")
    text(x + 10, PIPE_Y + 35, note, "s")
    if i:
        fig.arrow(f"M{x - PIPE_GAP + 2} {PIPE_Y + 22} H{x - 2}")

# ── x86 column ───────────────────────────────────────────────────────────────
COL_Y = 152
X86_X, X86_W = 20, 200
text(X86_X, COL_Y, "X86  (fib, n at [ebp+8])", "lbl")
ROW_H = 44
rows = [(addr, x86) for addr, x86, *_ in INSNS] + [TARGET]
for i, (addr, x86) in enumerate(rows):
    y = COL_Y + 12 + i * ROW_H + (14 if i == len(INSNS) else 0)
    body.append(f'<rect class="rung" x="{X86_X}" y="{y}" width="{X86_W}" height="{ROW_H - 6}" rx="5"/>')
    span = (insn_start[i], insn_end[i]) if i < len(INSNS) else (T_DONE, T_HOLD)
    body.append(f'<rect class="hl {window(*span)}" x="{X86_X}" y="{y}" width="{X86_W}" height="{ROW_H - 6}" rx="5"/>')
    text(X86_X + 10, y + 15, f"0x{addr:07x}", "s")
    text(X86_X + 10, y + 31, x86, "code sm")
    if i == len(INSNS):
        jump_y = y
text(X86_X, jump_y - 4, "branch target", "s")
fig.arrow(f"M{X86_X + X86_W + 4} {COL_Y + 12 + 2 * ROW_H + 19} "
          f"C{X86_X + X86_W + 18} {COL_Y + 12 + 2 * ROW_H + 19} {X86_X + X86_W + 18} {jump_y + 19} "
          f"{X86_X + X86_W + 4} {jump_y + 19}", window(T_DONE - STEP, T_HOLD))
text(X86_X, jump_y + 70, "17 P-code ops for 3 instructions:", "s")
text(X86_X, jump_y + 86, "every x86 flag is its own op.", "s")

# ── P-code column ────────────────────────────────────────────────────────────
PC_X, PC_W, OP_H = 236, 300, 22
text(PC_X, COL_Y, "P-CODE  (machine.pcodes[address])", "lbl")
body.append(f'<rect class="box" x="{PC_X}" y="{COL_Y + 12}" width="{PC_W}" height="{12 * OP_H + 12}" rx="6"/>')


def operand(x):
    return x if isinstance(x, str) else f"0x{x:X}"


for n, (_addr, _x86, _m, _b, ops) in enumerate(INSNS):
    group = window(insn_start[n], insn_end[n] if n < len(INSNS) - 1 else T_HOLD)
    parts = []
    for i, (opcode, out, ins) in enumerate(ops):
        y = COL_Y + 18 + i * OP_H
        if opcode == "Load":
            args = f"{out} ← ram[{ins[0]}]"
        elif opcode == "CBranch":
            args = f"→ {operand(ins[0])} if {ins[1]}"
        else:
            args = f"{out} ← {', '.join(operand(x) for x in ins)}"
        parts.append(f'<text x="{PC_X + 12}" y="{y + 15}" class="code sm f">{opcode}</text>'
                     f'<text x="{PC_X + 104}" y="{y + 15}" class="code sm">{escape(args)}</text>')
    body.append(f'<g class="{group}">{"".join(parts)}</g>')
for t, (n, i, *_rest) in zip(step_time, STEPS):
    y = COL_Y + 18 + i * OP_H
    body.append(f'<rect class="hl {window(t, t + STEP)}" x="{PC_X + 4}" y="{y}" width="{PC_W - 8}" height="{OP_H - 2}" rx="4"/>')

# ── Spaces column ────────────────────────────────────────────────────────────
SP_X, SP_W = 552, 208
text(SP_X, COL_Y, "SPACES  (BTreeMap<u64, u8>)", "lbl")
writes = {}  # name -> [(time, value)]
for t, (_n, _i, out, value, *_rest) in zip(step_time, STEPS):
    if out:
        writes.setdefault(out, []).append((t, value))


def cell(name, x, y, w, h, initial, fmt):
    """A space slot: its value changes on each write, with a flash."""
    history = writes.get(name, [])
    states = [(0, initial)] + [(t, fmt(v)) for t, v in history]
    for k, (t, shown) in enumerate(states):
        end = states[k + 1][0] if k + 1 < len(states) else T_HOLD
        cls = "code sm" + (" termdim" if shown == "·" else "")
        if k == 0:
            vis = track([(0, 1), (end, 0), (T_HOLD, 1), (PERIOD, 1)]) if end != T_HOLD else ""
        else:
            vis = window(t, end)
        body.append(f'<text x="{x + w - 8}" y="{y + h / 2 + 4.5}" class="{cls} {vis}" text-anchor="end">{escape(shown)}</text>')
    for t, _v in history:
        body.append(f'<rect class="hl {window(t, t + STEP)}" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/>')


def hex_of(name):
    return lambda v: f"{v:0{SIZE.get(name, 4) * 2}X}"


# register space
y0 = COL_Y + 12
body.append(f'<rect class="box" x="{SP_X}" y="{y0}" width="{SP_W}" height="96" rx="6"/>')
text(SP_X + 8, y0 + 16, "register", "s b")
for k, name in enumerate(["EAX", "EBP"]):
    y = y0 + 22 + k * 20
    text(SP_X + 10, y + 14, name, "code sm")
    cell(name, SP_X + 4, y, SP_W - 8, 19, f"{(0x80EF000 if name == 'EAX' else EBP):08X}", hex_of(name))
FLAG_W = (SP_W - 8) / len(FLAGS)
for k, name in enumerate(FLAGS):
    x = SP_X + 4 + k * FLAG_W
    text(x + FLAG_W / 2, y0 + 78, name, "s", "middle")
    history = writes.get(name, [])
    states = [(0, "·")] + [(t, str(v)) for t, v in history]
    for j, (t, shown) in enumerate(states):
        end = states[j + 1][0] if j + 1 < len(states) else T_HOLD
        vis = track([(0, 1), (end, 0), (T_HOLD, 1), (PERIOD, 1)]) if j == 0 else window(t, end)
        body.append(f'<text x="{x + FLAG_W / 2}" y="{y0 + 92}" class="code sm {vis}" text-anchor="middle">{shown}</text>')
    for t, _v in history:
        body.append(f'<rect class="hl {window(t, t + STEP)}" x="{x + 2}" y="{y0 + 66}" width="{FLAG_W - 4}" height="30" rx="4"/>')

# unique space
y1 = y0 + 106
body.append(f'<rect class="box" x="{SP_X}" y="{y1}" width="{SP_W}" height="{24 + len(UNIQUES) * 19}" rx="6"/>')
text(SP_X + 8, y1 + 16, "unique  (Sleigh temporaries)", "s b")
for k, name in enumerate(UNIQUES):
    y = y1 + 22 + k * 19
    text(SP_X + 10, y + 13.5, name, "code sm")
    cell(name, SP_X + 4, y, SP_W - 8, 18, "·", hex_of(name))

# ram space
y2 = y1 + 34 + len(UNIQUES) * 19
body.append(f'<rect class="box" x="{SP_X}" y="{y2}" width="{SP_W}" height="44" rx="6"/>')
text(SP_X + 8, y2 + 16, "ram", "s b")
text(SP_X + 10, y2 + 34, f"{EBP + 8:08X}", "code sm")
text(SP_X + SP_W - 10, y2 + 34, "0A 00 00 00", "code sm", "end")
load_times = [t for t, s in zip(step_time, STEPS) if INSNS[s[0]][4][s[1]][0] == "Load"]
for t in load_times:
    body.append(f'<rect class="hl {window(t, t + STEP)}" x="{SP_X + 4}" y="{y2 + 20}" width="{SP_W - 8}" height="20" rx="4"/>')

# ── Emulator log ─────────────────────────────────────────────────────────────
LOG_Y = 512
body.append(f'<rect class="term" x="20" y="{LOG_Y}" width="740" height="56" rx="6"/>')
text(32, LOG_Y + 19, "$ cargo run -- emulate ./tests/fib/bin", "code sm termdim " + window(0, T_RUN))
text(32, LOG_Y + 39, "loading section: .text", "code sm termdim " + window(T_LIFT + 2 * LIFT_STEP, T_RUN))
for k, (t, (_n, _i, _out, _v, head, log)) in enumerate(zip(step_time, STEPS)):
    end = step_time[k + 1] if k + 1 < len(step_time) else T_HOLD
    cls = window(t, end)
    body.append(f'<g class="{cls}"><text x="32" y="{LOG_Y + 22}" class="code sm termt" xml:space="preserve">{escape(head)}</text>'
                f'<text x="32" y="{LOG_Y + 42}" class="code sm termok" xml:space="preserve">{escape(log)}</text></g>')

# ── Phase captions ───────────────────────────────────────────────────────────
CAP_Y = fig.h - 22
for start, end, msg in [
    (0, T_RUN, "llvm-readobj finds .text and the fib symbol; Sleigh lifts every instruction to P-code before anything runs …"),
    (insn_start[0], insn_end[0], "… mov is three ops: add the offset, load n from ram, copy it into EAX …"),
    (insn_start[1], insn_end[1], "… cmp is twelve: the subtraction once, then each flag computed by its own match arm …"),
    (insn_start[2], T_DONE, "… and jge compares OF with SF, then CBranch returns PCodeControl::Branch."),
    (T_DONE, T_HOLD, "n = 10 ≥ 2, so the emulator jumps to 0x804975F and keeps walking fib's P-code."),
]:
    text(20, CAP_Y, msg, f"cap {window(start, end)}")

fig.write()
