#!/usr/bin/env python3
"""Animated figure: the flip paging simulator running a real request file.

Writes assets/figures/flip-paging.svg. Replays input_requests_1.txt (64 KB of
memory, 4 KB pages) with a small model of the program's rules, and checks the
model against what the real program printed. Terminal lines are copied from
that run (minus one long "not enough space" line).
"""
from math import ceil

from common import Figure

W, H = 780, 528
MEM, PAGE = 65536, 4096
N_FRAMES = MEM // PAGE

fig = Figure("flip-paging", W, H, period=26.0, label=(
    "Diagram of the flip paging simulator running input_requests_1.txt with 16 frames of 4 KB. "
    "Job 1 (9 pages) and jobs 2 to 8 fill memory; removing jobs 2, 4, 6 and 8 leaves holes that "
    "job 9's three pages fill. Job 10 needs six frames, so the oldest resident job, 1, is swapped "
    "out. Jobs 7 and 3 are suspended and 7 resumes into frame 7. Finally translate 9 5000 splits "
    "the address into page 2, offset 904, finds page 2 in frame 12, and prints physical address 45960."))
PERIOD = fig.period
HOLD = 25.2
text, window, track = fig.text, fig.window, fig.track

# ── The run: (request line, seconds on screen, terminal output) ───────────────
STEPS = [
    ("Job_ID  Size", 0.4, []),
    ("1  35000", 1.6, ["admit-job: id = 1, #pages = 9, internal-frag = 1864, size = 35000", "  admitted job"]),
    *[(f"{j}  4096", 0.32, [f"admit-job: id = {j}, #pages = 1, internal-frag = 0, size = 4096", "  admitted job"])
      for j in range(2, 9)],
    *[(f"{j}  0", 0.5, [f"suspend-job: id = {j}", "  suspended job"]) for j in (2, 4, 6, 8)],
    ("9  12000", 1.8, ["admit-job: id = 9, #pages = 3, internal-frag = 288, size = 12000", "  admitted job"]),
    ("10  24000", 3.6, ["admit-job: id = 10, #pages = 6, internal-frag = 576, size = 24000",
                        "suspend-job: id = 1", "  suspended job", "  admitted job"]),
    ("7  -1", 0.7, ["suspend-job: id = 7", "  suspended job"]),
    ("3  -1", 0.7, ["suspend-job: id = 3", "  suspended job"]),
    ("print", 1.6, ["Free frames: 7, 8, 9, 11, 15, 16", "Total Internal Fragmentation (Resident): 2728 bytes.",
                    "Resident Job Queue: 5, 9, 10"]),
    ("7  -2", 1.2, ["resume-job: 7", "  resumed job"]),
    ("print", 0.9, ["Free frames: 8, 9, 11, 15, 16", "Resident Job Queue: 5, 9, 10, 7"]),
    ("translate 10 5000", 1.0, ["  page-number      = 2", "  offset           = 904",
                                "  frame-number     = 2", "  physical-address = 5000"]),
    ("translate 9 5000", 4.6, ["  page-number      = 2", "  offset           = 904",
                               "  frame-number     = 12", "  physical-address = 45960"]),
    ("translate 9 12100", 0.9, ["address outside of job's pages"]),
    ("translate 1 100", 0.9, ["job is not resident"]),
]
T0 = 0.4
step_t = []
t = T0
for _line, dur, _out in STEPS:
    step_t.append(t)
    t += dur
T_END = t
assert T_END < HOLD - 0.4, "timeline overruns the loop"

# ── Model of the simulator, recording when each frame changes ─────────────────
frames = [None] * N_FRAMES       # (job, page) or None
queue, jobs, n_pages = [], {}, {}
spans = [[] for _ in range(N_FRAMES)]  # per frame: [start, end, job, page]
queue_log = [(0, [])]
evictions = []                   # (start, end, job)


def place(f, job, page, at):
    frames[f] = (job, page)
    spans[f].append([at, None, job, page])


def free(job, at):
    for f, occ in enumerate(frames):
        if occ and occ[0] == job:
            frames[f] = None
            spans[f][-1][1] = at
    jobs[job] = "suspended"
    if job in queue:
        queue.remove(job)
    queue_log.append((at, list(queue)))


def swap_in(job, at, evict_at=None):
    pages = n_pages[job]
    while pages > frames.count(None):
        victim = queue[0]
        evictions.append((evict_at, at - 0.1, victim))
        free(victim, at - 0.1)
    page = 0
    for f in range(N_FRAMES):
        if frames[f] is None and page < pages:
            place(f, job, page + 1, at)
            page += 1
    queue.append(job)
    jobs[job] = "resident"
    queue_log.append((at, list(queue)))


for (line, dur, _out), at in zip(STEPS, step_t):
    words = line.split()
    if words[0] in ("Job_ID", "print", "translate"):
        continue
    job, size = int(words[0]), int(words[1])
    if size > 0:
        n_pages[job] = ceil(size / PAGE)
        if job == 10:
            swap_in(job, at + 2.1, evict_at=at + 0.7)
        else:
            swap_in(job, at + 0.25)
    elif size == 0:
        free(job, at + 0.25)
        del jobs[job]
    elif size == -1:
        free(job, at + 0.25)
    elif size == -2:
        swap_in(job, at + 0.35)

# What the real program printed after the last request.
assert [f"{o[0]}.{o[1]}" if o else "-" for o in frames] == \
    "10.1 10.2 10.3 10.4 10.5 10.6 7.1 - - 9.1 - 9.2 5.1 9.3 - -".split()
assert queue == [5, 9, 10, 7]
for s in spans:
    for sp in s:
        sp[1] = HOLD if sp[1] is None else sp[1]

fig.header("flip — the paging simulator, running for real",
           "CSCI 460 assignment 1: 64 KB of memory in 4 KB frames, jobs paged in and swapped out FIFO. Replaying input_requests_1.txt.")

# ── Request file ──────────────────────────────────────────────────────────────
LIST_X, LIST_Y, LINE_H, LIST_W = 20, 84, 15.4, 156
text(LIST_X, LIST_Y, "INPUT_REQUESTS_1.TXT", "lbl")
fig.add(f'<rect class="box" x="{LIST_X}" y="{LIST_Y + 8}" width="{LIST_W}" height="{len(STEPS) * LINE_H + 12}" rx="6"/>')
for i, ((line, dur, _out), at) in enumerate(zip(STEPS, step_t)):
    y = LIST_Y + 14 + i * LINE_H
    fig.add(f'<rect class="hl {window(at, at + dur)}" x="{LIST_X + 4}" y="{y}" width="{LIST_W - 8}" height="{LINE_H}" rx="3"/>')
    done = track([(0, 1), (at, 1), (at + dur, 0.55), (HOLD, 0.55), (HOLD + 0.2, 1), (PERIOD, 1)])
    fig.runs(LIST_X + 12, y + 11.5, [("m" if i == 0 else "", line)], f"code sm {done}")

# ── Frames ───────────────────────────────────────────────────────────────────
RX = 200
CELL_W, CELL_H, GAP = 64, 50, 6
text(RX, LIST_Y, "PHYSICAL MEMORY  (16 frames × 4 KB)", "lbl")
cell_xy = []
for f in range(N_FRAMES):
    x = RX + (f % 8) * (CELL_W + GAP)
    y = LIST_Y + 8 + (f // 8) * (CELL_H + 8)
    cell_xy.append((x, y))
    fig.add(f'<rect class="box" x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="5"/>')

for f, (x, y) in enumerate(cell_xy):
    busy = sorted((s, e) for s, e, _j, _p in spans[f])
    gaps, cur = [], 0
    for s, e in busy:
        if s > cur:
            gaps.append((cur, s))
        cur = e
    if cur < HOLD:
        gaps.append((cur, HOLD))
    for s, e in gaps:
        cls = track([(0, 1), (e, 0), (PERIOD, 0)]) if s == 0 else window(s, e)
        text(x + CELL_W / 2, y + 36, "free", f"s {cls}", "middle")
    for s, e, job, page in spans[f]:
        fig.add(f'<g class="{window(s, e)}"><rect class="hl" x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="5"/>'
                f'<text x="{x + CELL_W / 2}" y="{y + 37}" class="code sm b" text-anchor="middle">J{job} p{page}</text></g>')
    text(x + 6, y + 14, f"f{f + 1}", "s")

for start, end, job in evictions:
    for f, (x, y) in enumerate(cell_xy):
        if any(j == job and s <= start < e for s, e, j, _p in spans[f]):
            fig.add(f'<rect class="bad {window(start, end)}" x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="5"/>')

# ── Resident queue ───────────────────────────────────────────────────────────
Q_Y = LIST_Y + 8 + 2 * CELL_H + 8 + 34
text(RX, Q_Y, "RESIDENT QUEUE  (oldest is swapped out first)", "lbl")
CHIP_W = 40
for i, (at, q) in enumerate(queue_log):
    end = queue_log[i + 1][0] if i + 1 < len(queue_log) else HOLD
    if end <= at:
        continue
    if not q:
        text(RX, Q_Y + 26, "(empty)", f"s {window(at, end)}")
        continue
    chips = "".join(
        f'<rect class="chip" x="{RX + k * (CHIP_W + 6)}" y="{Q_Y + 8}" width="{CHIP_W}" height="26" rx="5"/>'
        f'<text x="{RX + k * (CHIP_W + 6) + CHIP_W / 2}" y="{Q_Y + 26}" class="code sm" text-anchor="middle">J{j}</text>'
        for k, j in enumerate(q))
    fig.add(f'<g class="{window(at, end)}">{chips}</g>')
for start, end, job in evictions:
    fig.add(f'<rect class="bad {window(start, end)}" x="{RX}" y="{Q_Y + 8}" width="{CHIP_W}" height="26" rx="5"/>')
    text(RX + 5 * (CHIP_W + 6) + 6, Q_Y + 26, f"job {job} → secondary storage", f"badt sm {window(start, end + 0.6)}")

# ── Terminal output ──────────────────────────────────────────────────────────
TERM_Y = Q_Y + 58
TERM_LINE = 16.5
fig.add(f'<rect class="term" x="{RX}" y="{TERM_Y}" width="{W - 20 - RX}" height="{4 * TERM_LINE + 14}" rx="6"/>')
for (line, dur, out), at in zip(STEPS, step_t):
    if not out:
        continue
    cls = window(at, at + dur)
    for k, s in enumerate(out):
        tone = "termerr" if s in ("address outside of job's pages", "job is not resident") else "termt"
        fig.runs(RX + 12, TERM_Y + 20 + k * TERM_LINE, [(tone, s)], f"code sm {cls}")

# ── Address translation ─────────────────────────────────────────────────────
TR_Y = TERM_Y + 4 * TERM_LINE + 14 + 30
text(RX, TR_Y, "ADDRESS TRANSLATION", "lbl")
i_tr = next(i for i, s in enumerate(STEPS) if s[0] == "translate 9 5000")
t_tr, d_tr = step_t[i_tr], STEPS[i_tr][1]
LINES = [
    [("", "translate 9 "), ("num", "5000"), ("", "  →  5000 = 1 × 4096 + "), ("num", "904"),
     ("m", "     page 2, offset 904")],
    [("", "job 9's page table:  p1 → f10   "), ("b", "p2 → f12"), ("", "   p3 → f14")],
    [("", "f12 starts at 11 × 4096 = 45056;  45056 + 904 = "), ("ok", "45960")],
]
for k, parts in enumerate(LINES):
    start = t_tr + 0.3 + k * 1.1
    fig.runs(RX, TR_Y + 22 + k * 20, parts, f"code sm {window(start, T_END + 0.3)}")
f12x, f12y = cell_xy[11]
fig.add(f'<rect class="hl {window(t_tr + 1.4, t_tr + d_tr)}" x="{f12x - 3}" y="{f12y - 3}" width="{CELL_W + 6}" height="{CELL_H + 6}" rx="7"/>')
text(RX, TR_Y + 22, "shown for translate commands", f"s {track([(0, 1), (t_tr, 0), (PERIOD, 0)])}")

# ── Phase captions ───────────────────────────────────────────────────────────
CAP_Y = H - 18
i9 = next(i for i, s in enumerate(STEPS) if s[0] == "9  12000")
i10 = i9 + 1
i_sus = i10 + 1
i_tr10 = i_tr - 1
for start, end, msg in [
    (0, step_t[i9], "Every job is cut into 4 KB pages; each page takes the first free frame."),
    (step_t[i9], step_t[i10], "Removing jobs leaves holes, and job 9's pages fill them — frames needn't be contiguous."),
    (step_t[i10], step_t[i_sus], "Job 10 needs 6 frames but only 1 is free, so the oldest resident job is swapped out."),
    (step_t[i_sus], step_t[i_tr10], "Suspending frees a job's frames; resuming pages it back into whatever is free."),
    (step_t[i_tr10], T_END, "translate splits an address into page and offset, then looks the page up in the job's table."),
    (T_END, HOLD, "Same rules, written once in C, once in Python, and once in a language I made up."),
]:
    text(20, CAP_Y, msg, f"cap {window(start, end)}")

fig.write()
