#!/usr/bin/env python3
"""Animated figure: reading flip, the language I wrote for an OS assignment.

Writes assets/figures/flip-syntax.svg. The code is swap-job-in from the paging
simulator in dillon-shaffer-1.flip, minus one status message.
"""
from common import Figure

W, H = 780, 594
fig = Figure("flip-syntax", W, H, period=22.0, label=(
    "Diagram of flip syntax, using swap-job-in from a paging simulator. Functions are "
    "'name does … end-name'; 's and s' are property access; 's result calls a method and "
    "'do f of a & b' calls a function; let's … let's-be-done is a block; strings choose their "
    "own delimiter with String X … X and comments start with NOTE:; loop over binds loop's item; "
    "then chains statements; 'hi x becomes it plus 1' reassigns using it for the old value."))
HOLD = 21.0

CODE = """\
swap-job-in does
  s job do-be my args

  loop while job's pages greater-than s' n-free-frames let's
    NOTE: exit if job-queue becomes empty (job should be checked that it can fit)
    if s' queue is-empty
      do print-simulator-state of s
      then ABORT with String X unreachable: job queue is empty. the job can't fit! X

    job-id do-be s's queue's pop-front's result
    do suspend-job of s & job-id
  let's-be-done

  i do-be 0
  loop over s's frames
    f do-be loop's item
    then if f's job-id is FRAME_FREE
      hi f's job-id becomes job's id
      then hi f's page becomes i
      then hi i becomes it plus 1
      then if i is job's pages break

  do s's queue's add of job's id
  hi s's n-free-frames becomes it minus job's pages
  hi job's status becomes STATUS_RESIDENT
end-swap-job-in""".splitlines()

KEYWORDS = {
    "does", "do-be", "do", "of", "with", "&", "if", "then", "loop", "over", "while", "let's",
    "let's-be-done", "hi", "becomes", "it", "break", "ABORT", "is", "is-empty", "greater-than",
    "plus", "minus", "my", "result", "String",
}


def highlight(line):
    """Split one line of flip into (class, text) runs."""
    indent = line[: len(line) - len(line.lstrip())]
    words = line.split()
    if words and words[0] == "NOTE:":
        return [("", indent), ("cm", line.strip())]
    runs = [("", indent)]
    i = 0
    while i < len(words):
        w = words[i]
        if w == "String":
            delim = words[i + 1]
            end = words.index(delim, i + 2)
            runs += [("k", "String "), ("str", " ".join(words[i + 1:end + 1]))]
            i = end + 1
        elif w in KEYWORDS or w.startswith("end-"):
            runs.append(("k", w))
            i += 1
        elif w.endswith("'s") and w[:-2] in KEYWORDS:
            runs += [("k", w[:-2]), ("f", "'s")]
            i += 1
        elif w.endswith("'s"):
            runs += [("", w[:-2]), ("f", "'s")]
            i += 1
        elif w.endswith("s'"):
            runs += [("", w[:-1]), ("f", "'")]
            i += 1
        elif w.lstrip("-").isdigit() or w.isupper():
            runs.append(("num", w))
            i += 1
        else:
            runs.append(("", w))
            i += 1
        runs.append(("", " "))
    return runs[:-1]


# Each step: (rows to highlight, {row: python equivalent}, caption runs)
STEPS = [
    ([0, 1, 25], {0: "def swap_job_in(*args):", 1: "s, job = args"},
     [("", "Functions are "), ("code", "name does … end-name"), ("", "; "), ("code", "my args"),
      ("", " unpacks the arguments.")]),
    ([3], {3: "while job.pages > s.n_free_frames:"},
     [("code", "'s"), ("", " reads a property, and names ending in s get "), ("code", "s'"),
      ("", " — it's possessive.")]),
    ([3, 11], {11: "# end of the while body"},
     [("code", "let's"), ("", " … "), ("code", "let's-be-done"),
      ("", " is a block. Without one, a body is a single statement.")]),
    ([4, 7], {7: "abort(...)"},
     [("", "Comments start with "), ("code", "NOTE:"), ("", ". Strings pick their own delimiter: "),
      ("code", "String X … X"), ("", ".")]),
    ([9, 10], {9: "job_id = s.queue.pop_front()", 10: "suspend_job(s, job_id)"},
     [("code", "'s result"), ("", " calls a method, and "), ("code", "do f of a & b"),
      ("", " calls a function.")]),
    ([14, 15], {14: "for f in s.frames:", 15: "f = <current item>"},
     [("code", "loop over"), ("", " iterates, and "), ("code", "loop's item"), ("", " / "),
      ("code", "loop's index"), ("", " name where it is.")]),
    ([16, 17, 18, 19, 20], {16: "if f.job_id == FRAME_FREE:"},
     [("code", "then"), ("", " chains statements, so one "), ("code", "if"), ("", " or "),
      ("code", "loop"), ("", " can own several.")]),
    ([17, 18, 19, 23], {17: "f.job_id = job.id", 19: "i += 1", 23: "s.n_free_frames -= job.pages"},
     [("code", "hi x becomes …"), ("", " reassigns, and "), ("code", "it"),
      ("", " is the value being replaced.")]),
]
STEP_T0, STEP_LEN = 0.6, 2.45
assert STEP_T0 + len(STEPS) * STEP_LEN < HOLD - 0.5, "timeline overruns the loop"

fig.header("flip — a language I wrote for one OS assignment",
           "CSCI 460's paging simulator, written in flip: its own tokenizer, parser and interpreter, all in one Python file.")

# ── Code panel ──────────────────────────────────────────────────────────────
PANEL_Y, LINE_H, CODE_X = 76, 17, 36
panel_h = len(CODE) * LINE_H + 36
fig.add(f'<rect class="box" x="20" y="{PANEL_Y}" width="{W - 40}" height="{panel_h}" rx="6"/>')
fig.text(W - 34, PANEL_Y + 18, "PYTHON, ROUGHLY", "lbl", "end")


def row_y(r):
    return PANEL_Y + 28 + r * LINE_H


for i, (rows, ghosts, _cap) in enumerate(STEPS):
    start = STEP_T0 + i * STEP_LEN
    end = start + STEP_LEN
    on = fig.window(start, end)
    for r in rows:
        width = len(CODE[r]) * 7.25 + 16
        fig.add(f'<rect class="hl {on}" x="{CODE_X - 8}" y="{row_y(r) - 1}" width="{width:.0f}" height="{LINE_H}" rx="3"/>')
    for r, py in ghosts.items():
        cls = fig.track([(0, 0), (start, 1), (end, 0.6), (HOLD, 0.6), (HOLD + 0.2, 0), (fig.period, 0)])
        fig.text(W - 34, row_y(r) + 12, py, f"code sm cm {cls}", "end")

for r, line in enumerate(CODE):
    if line:
        fig.runs(CODE_X, row_y(r) + 12, highlight(line), "code sm")

# ── Captions ────────────────────────────────────────────────────────────────
CAP_Y = PANEL_Y + panel_h + 30
for i, (_rows, _ghosts, cap) in enumerate(STEPS):
    start = STEP_T0 + i * STEP_LEN
    fig.runs(20, CAP_Y, cap, f"cap {fig.window(start, start + STEP_LEN)}")
fig.runs(20, CAP_Y, [("", "It started as a joke. Then I wrote the whole assignment in it — "),
                     ("code", "dillon-shaffer-1.flip"), ("", ".")],
         f"cap {fig.window(STEP_T0 + len(STEPS) * STEP_LEN, HOLD)}")

fig.write()
