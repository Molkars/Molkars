#!/usr/bin/env python3
"""Animated figure: Notch stack traces that interleave Java and Notch frames.

Writes assets/figures/notch-traces.svg. A Java program runs a Notch script that
calls back into Java, which calls a Notch closure that divides by zero.

BEFORE is the real trace printed by Notch's main branch for this program.
AFTER is the interleaved trace the new StackTracer (in development) is built to
produce, in the formats NotchStackTraceElement uses: `notch/<file>:<line>` for
Notch frames and StackTraceElement.toString() for Java frames.
"""
from common import Figure

NOTCH_SRC = """function withTax(price)
  return price * 100 / (price - 20)
end

function report(prices)
  tax = \\ p -> withTax(p)
  return app.Orders.total(prices, tax)
end

print(report([10, 30, 20]))"""

MAIN_SRC = [
    (7, 'public class Main {'),
    (8, '    public static void main(String[] args) throws Exception {'),
    (9, '        runReport(Files.readString(Path.of("report.notch")));'),
    (10, '    }'),
    (11, ''),
    (12, '    static void runReport(String src) {'),
    (13, '        Notch.run(new Source("report.notch", src));'),
    (14, '    }'),
    (15, '}'),
]  # app/Main.java
ORDERS_SRC = [
    (6, 'public class Orders {'),
    (7, '    public static int total(List<Integer> prices,'),
    (8, '                            Function<Integer, Integer> tax) {'),
    (9, '        int sum = 0;'),
    (10, '        for (int p : prices) sum += tax.apply(p);'),
    (11, '        return sum;'),
    (12, '    }'),
    (13, '}'),
]  # app/Orders.java

BEFORE = """java.base/java.lang.Thread.getStackTrace(Thread.java:2193)
edu.montana.notch.chisel.Diagnostic.<init>(Diagnostic.java:19)
edu.montana.notch.runtime.NotchRuntime.execute(NotchRuntime.java:237)
edu.montana.notch.runtime.NotchClosure.call(NotchClosure.java:34)
edu.montana.notch.expressions.NotchMethodInvocationExpression.evaluate(NotchMethodInvocationExpression.java:59)
edu.montana.notch.runtime.NotchRuntime.evaluate(NotchRuntime.java:226)
edu.montana.notch.runtime.NotchClosure.call(NotchClosure.java:30)
edu.montana.notch.runtime.NotchClosure.apply(NotchClosure.java:70)
app.Orders.total(Orders.java:10)
java.base/jdk.internal.reflect.DirectMethodHandleAccessor.invoke(DirectMethodHandleAccessor.java:104)
java.base/java.lang.reflect.Method.invoke(Method.java:565)
edu.montana.notch.types.NotchJavaMethod.invoke(NotchJavaMethod.java:71)
edu.montana.notch.runtime.NotchBoundMethod.invoke(NotchBoundMethod.java:9)
edu.montana.notch.expressions.NotchMethodInvocationExpression.evaluate(NotchMethodInvocationExpression.java:55)
edu.montana.notch.runtime.NotchRuntime.evaluate(NotchRuntime.java:226)
edu.montana.notch.statements.NotchReturn.execute(NotchReturn.java:18)
edu.montana.notch.runtime.NotchRuntime.execute(NotchRuntime.java:232)
edu.montana.notch.runtime.NotchClosure.call(NotchClosure.java:34)
edu.montana.notch.expressions.NotchMethodInvocationExpression.evaluate(NotchMethodInvocationExpression.java:59)
edu.montana.notch.runtime.NotchRuntime.evaluate(NotchRuntime.java:226)
edu.montana.notch.statements.NotchPrint.execute(NotchPrint.java:20)
edu.montana.notch.runtime.NotchRuntime.execute(NotchRuntime.java:232)
edu.montana.notch.statements.NotchStatements.execute(NotchStatements.java:21)
edu.montana.notch.runtime.NotchRuntime.execute(NotchRuntime.java:232)
edu.montana.notch.Notch.run(Notch.java:93)
edu.montana.notch.Notch.run(Notch.java:82)
app.Main.runReport(Main.java:13)
app.Main.main(Main.java:9)""".splitlines()

# The call chain, outermost first: (frame text in the new trace, language, what it is, code panel, line)
CALLS = [
    ("app.Main.main(Main.java:9)", "java", "main", "main", 9),
    ("app.Main.runReport(Main.java:13)", "java", "runReport", "main", 13),
    ("notch/report.notch:10", "notch", "top level", "notch", 10),
    ("notch/report.notch:7", "notch", "report", "notch", 7),
    ("app.Orders.total(Orders.java:10)", "java", "Orders.total", "orders", 10),
    ("notch/report.notch:6", "notch", "tax closure", "notch", 6),
    ("notch/report.notch:2", "notch", "withTax", "notch", 2),
]

W, H = 780, 896
STEP = 0.9
T_CALL = [0.4 + i * STEP for i in range(len(CALLS))]
T_THROW = T_CALL[-1] + 0.9
T_BEFORE, BEFORE_STEP = T_THROW + 0.8, 0.06
T_AFTER = T_BEFORE + len(BEFORE) * BEFORE_STEP + 0.8
AFTER_STEP = 0.5
T_DONE = T_AFTER + (len(CALLS) + 1) * AFTER_STEP
HOLD = T_DONE + 4.0
fig = Figure("notch-traces", W, H, period=round(HOLD + 0.6, 1), label=(
    "Diagram of Notch stack traces across Java and Notch. Java's main runs report.notch, whose report "
    "function calls the Java method Orders.total, which calls a Notch closure that calls withTax and "
    "divides by zero. Today's trace is 28 JVM frames with only three of the program's own frames; the new "
    "tracer, in development, prints 7 frames that alternate between Java and Notch in call order."))


def until_hold(t):
    return fig.window(t, HOLD)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


fig.header("Notch — one stack trace across Java and Notch",
           "A tracer I'm building for Notch: errors report the frames you wrote, in order, whichever "
           "language they're in.")
fig.css.append(".xs { font-size: 10.5px; } .xxs { font-size: 9px; } "
               ".jv { fill: #953800; } .nt { fill: #8250df; } .tjv { fill: #ffa657; } .tnt { fill: #d2a8ff; } "
               "@media (prefers-color-scheme: dark) { .jv { fill: #ffa657; } .nt { fill: #d2a8ff; } }")

# ── Code panels ──────────────────────────────────────────────────────────────
CODE_Y = 90
NX, NW = 20, 288
JX, JW = 320, W - 20 - 320
LH = 15
fig.text(NX, CODE_Y - 8, "NOTCH  report.notch", "lbl")
notch_lines = NOTCH_SRC.splitlines()
NH = len(notch_lines) * LH + 18
MAIN_Y = CODE_Y
MAIN_H = len(MAIN_SRC) * LH + 18
ORD_Y = MAIN_Y + MAIN_H + 26
ORD_H = len(ORDERS_SRC) * LH + 18
panel_h = ORD_Y + ORD_H - CODE_Y
fig.add(f'<rect class="box" x="{NX}" y="{CODE_Y}" width="{NW}" height="{panel_h}" rx="6"/>')
fig.text(JX, MAIN_Y - 8, "JAVA  app/Main.java", "lbl")
fig.add(f'<rect class="box" x="{JX}" y="{MAIN_Y}" width="{JW}" height="{MAIN_H}" rx="6"/>')
fig.text(JX, ORD_Y - 8, "JAVA  app/Orders.java", "lbl")
fig.add(f'<rect class="box" x="{JX}" y="{ORD_Y}" width="{JW}" height="{ORD_H}" rx="6"/>')


def line_box(panel, line):
    if panel == "notch":
        return NX, CODE_Y + 9 + (line - 1) * LH, NW
    rows, top = (MAIN_SRC, MAIN_Y) if panel == "main" else (ORDERS_SRC, ORD_Y)
    idx = [n for n, _ in rows].index(line)
    return JX, top + 9 + idx * LH, JW


# Highlight each frame's line while it is the innermost call, and keep a faint mark after.
for i, (_f, lang, _what, panel, line) in enumerate(CALLS):
    x, y, w = line_box(panel, line)
    end = T_CALL[i + 1] if i + 1 < len(CALLS) else T_THROW
    fig.add(f'<rect class="hl {fig.window(T_CALL[i], end)}" x="{x + 4}" y="{y}" width="{w - 8}" height="{LH}" rx="3"/>')
x, y, w = line_box("notch", 2)
fig.add(f'<rect class="bad {fig.window(T_THROW - 0.1, T_AFTER)}" x="{x + 4}" y="{y}" width="{w - 8}" height="{LH}" rx="3"/>')
fig.add(f'<text x="{x + w - 10}" y="{y + 11}" class="code xs badt b {fig.window(T_THROW - 0.1, T_AFTER)}" '
        f'text-anchor="end">/ by zero</text>')

NOTCH_KW = {"function", "return", "end"}
for n, text in enumerate(notch_lines, 1):
    parts, word = [], ""
    for ch in text + " ":
        if ch.isalnum() or ch == "_":
            word += ch
            continue
        if word:
            parts.append(("k" if word in NOTCH_KW else "f" if word in ("withTax", "report", "print") else
                          "num" if word.isdigit() else "", word))
            word = ""
        parts.append(("", ch))
    spans = "".join(f'<tspan class="{c}">{esc(s)}</tspan>' if c else esc(s) for c, s in parts)
    fig.add(f'<text x="{NX + 8}" y="{CODE_Y + 9 + (n - 1) * LH + 11}" class="code xs" xml:space="preserve">'
            f'<tspan class="cm">{n} </tspan>{spans}</text>')
JAVA_KW = {"public", "static", "void", "int", "var", "for", "throws", "return", "class"}
for rows, top in ((MAIN_SRC, MAIN_Y), (ORDERS_SRC, ORD_Y)):
    for i, (n, text) in enumerate(rows):
        parts, word = [], ""
        for ch in text + " ":
            if ch.isalnum() or ch == "_":
                word += ch
                continue
            if word:
                parts.append(("k" if word in JAVA_KW else "", word))
                word = ""
            parts.append(("", ch))
        spans = "".join(f'<tspan class="{c}">{esc(s)}</tspan>' if c else esc(s) for c, s in parts)
        fig.add(f'<text x="{JX + 8}" y="{top + 9 + i * LH + 11}" class="code xs" xml:space="preserve">'
                f'<tspan class="cm">{n:>2} </tspan>{spans}</text>')

# ── Call stack strip ─────────────────────────────────────────────────────────
STRIP_Y = CODE_Y + panel_h + 36
fig.text(20, STRIP_Y - 8, "CALL STACK  (outermost → innermost)", "lbl")
CHIP_GAP = 8
chip_w = (W - 40 - CHIP_GAP * (len(CALLS) - 1)) / len(CALLS)
chip_x = [20 + i * (chip_w + CHIP_GAP) for i in range(len(CALLS))]
for i, (_f, lang, what, *_r) in enumerate(CALLS):
    x = chip_x[i]
    cls = "jv" if lang == "java" else "nt"
    fig.add(f'<g class="{until_hold(T_CALL[i])}"><rect class="chip" x="{x:.1f}" y="{STRIP_Y}" width="{chip_w:.1f}" '
            f'height="40" rx="6"/><text x="{x + chip_w / 2:.1f}" y="{STRIP_Y + 16}" class="xxs b {cls}" '
            f'text-anchor="middle">{"JAVA" if lang == "java" else "NOTCH"}</text>'
            f'<text x="{x + chip_w / 2:.1f}" y="{STRIP_Y + 31}" class="code xxs" text-anchor="middle">{esc(what)}</text></g>')
    if i:
        fig.add(f'<path class="edge {until_hold(T_CALL[i])}" d="M{x - CHIP_GAP + 1:.1f} {STRIP_Y + 20} H{x - 1:.1f}" '
                f'marker-end="url(#arr)"/>')
fig.add(f'<rect class="bad {until_hold(T_THROW)}" x="{chip_x[-1]:.1f}" y="{STRIP_Y}" width="{chip_w:.1f}" height="40" rx="6"/>')

# ── Before / after traces ────────────────────────────────────────────────────
TR_Y = STRIP_Y + 74
TR_H = H - TR_Y - 46
BX, BW = 20, 372
AX, AW = 404, W - 20 - 404
fig.text(BX, TR_Y - 8, "TODAY  (main branch, real output)", "lbl")
fig.text(AX, TR_Y - 8, "NEW TRACER", "lbl")
fig.add(f'<rect class="node" x="{AX + 82}" y="{TR_Y - 20}" width="96" height="16" rx="8"/>'
        f'<text x="{AX + 130}" y="{TR_Y - 8}" class="s b" text-anchor="middle">in development</text>')
fig.add(f'<rect class="term" x="{BX}" y="{TR_Y}" width="{BW}" height="{TR_H}" rx="6"/>')
fig.add(f'<rect class="term" x="{AX}" y="{TR_Y}" width="{AW}" height="{TR_H}" rx="6"/>')

BLH = (TR_H - 46) / len(BEFORE)
MAX_CHARS = 63
fig.add(f'<text x="{BX + 10}" y="{TR_Y + 15}" class="code xxs termerr {until_hold(T_BEFORE - 0.3)}">'
        f'note: threw a java.lang.ArithmeticException · / by zero</text>')
for i, frame in enumerate(BEFORE):
    mine = frame.startswith("app.")
    text = frame if len(frame) <= MAX_CHARS else frame[: MAX_CHARS - 1] + "…"
    cls = "termt b" if mine else "termdim"
    style = "" if mine else ' style="opacity:.55"'
    fig.add(f'<text x="{BX + 10}" y="{TR_Y + 28 + i * BLH:.1f}" class="code xxs {cls} {until_hold(T_BEFORE + i * BEFORE_STEP)}"'
            f'{style} xml:space="preserve">- {esc(text)}</text>')
fig.add(f'<text x="{BX + BW - 10}" y="{TR_Y + TR_H - 8}" class="code xxs termerr b {until_hold(T_AFTER - 0.4)}" '
        f'text-anchor="end">28 frames · 3 are yours · no Notch frames</text>')

ALH = 21
fig.add(f'<text x="{AX + 12}" y="{TR_Y + 22}" class="code xs termerr b {until_hold(T_AFTER)}">'
        f'java.lang.ArithmeticException: / by zero</text>')
for k, (frame, lang, what, *_r) in enumerate(reversed(CALLS)):
    i = len(CALLS) - 1 - k
    t = T_AFTER + (k + 1) * AFTER_STEP
    y = TR_Y + 22 + (k + 1) * ALH
    cls = "tjv" if lang == "java" else "tnt"
    fig.add(f'<g class="{until_hold(t)}"><text x="{AX + 12}" y="{y}" class="code xs termt" xml:space="preserve">'
            f'    at <tspan class="{cls}">{esc(frame)}</tspan></text>'
            f'<text x="{AX + AW - 10}" y="{y}" class="code xxs termdim" text-anchor="end">{esc(what)}</text></g>')
    fig.add(f'<rect class="hl {fig.window(t, t + AFTER_STEP)}" x="{chip_x[i]:.1f}" y="{STRIP_Y}" width="{chip_w:.1f}" '
            f'height="40" rx="6"/>')
fig.add(f'<text x="{AX + AW - 10}" y="{TR_Y + TR_H - 8}" class="code xxs termok b {until_hold(T_DONE)}" '
        f'text-anchor="end">7 frames · every one yours · in call order</text>')

# ── Captions ─────────────────────────────────────────────────────────────────
for start, end, msg in [
    (0, T_THROW, "Java runs a Notch script, Notch calls back into Java, and Java calls a Notch closure …"),
    (T_THROW, T_AFTER, "… which divides by zero. Today that's 28 JVM frames, mostly the interpreter's own …"),
    (T_AFTER, HOLD, "… the new tracer splices Notch call sites into the Java trace, so you see your 7 frames, in order."),
]:
    fig.text(20, H - 18, msg, f"cap {fig.window(start, end)}")

fig.write()
