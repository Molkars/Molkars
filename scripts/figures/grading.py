#!/usr/bin/env python3
"""Animated figure: three grading pipelines I built or contributed to at MSU.

Writes assets/figures/grading.svg. Three scenes cycle in one frame. Stage names
match the real code; every student name, id, and grade shown is a placeholder.
"""
from common import Figure

W, H = 780, 470
SCENE = 9.0
fig = Figure("grading", W, H, period=3 * SCENE, label=(
    "Diagram of three grading pipelines. CSCI 476: a script injected into the D2L grade page posts "
    "student names to a local Rust server, which fuzzy-matches them against the classlist and fills "
    "in pwn.college grades. CSCI 468: each push runs the course autograder and publishes results as a "
    "GitHub release; my anticheat workflow snapshots any edited release and opens an issue. CSCI 366: "
    "the grader caches test suites by release time, runs every test in isolation, and exports a grades "
    "CSV. All names and grades shown are placeholders."))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def win(scene, start=0.0, end=None):
    s0 = scene * SCENE
    return fig.window(s0 + start, s0 + (SCENE - 0.3 if end is None else end))


fig.header("Grading at scale — three pipelines",
           "Course tooling from MSU. Badges mark the parts I wrote; names and grades are placeholders.")
fig.css.append(".xs { font-size: 11px; }")

TABS = [("CSCI 476", "pwn.college → D2L"), ("CSCI 468", "autograde + anticheat"), ("CSCI 366", "isolated test runs")]
TAB_W = (W - 40 - 16) / 3
for i, (name, sub) in enumerate(TABS):
    x = 20 + i * (TAB_W + 8)
    fig.add(f'<rect class="chip" x="{x:.1f}" y="70" width="{TAB_W:.1f}" height="36" rx="6"/>')
    fig.add(f'<rect class="hl {win(i, 0, SCENE)}" x="{x:.1f}" y="70" width="{TAB_W:.1f}" height="36" rx="6"/>')
    fig.text(x + 12, 86, name, "sm b")
    fig.text(x + 12, 100, sub, "s")

STAGE_Y, STAGE_H = 132, 58
TERM_Y, TERM_H = 230, 178


def scene(i, stages, step, term):
    """stages: (title, subtitle, mine). Each lights up in turn; term: (t, cls, text) lines."""
    n = len(stages)
    gap = 14
    w = (W - 40 - gap * (n - 1)) / n
    for j, (title, sub, mine) in enumerate(stages):
        x = 20 + j * (w + gap)
        t = 0.3 + j * step
        fig.add(f'<g class="{win(i)}"><rect class="box" x="{x:.1f}" y="{STAGE_Y}" width="{w:.1f}" height="{STAGE_H}" rx="6"/>'
                f'<text x="{x + w / 2:.1f}" y="{STAGE_Y + 24}" class="code xs b" text-anchor="middle">{esc(title)}</text>'
                f'<text x="{x + w / 2:.1f}" y="{STAGE_Y + 42}" class="s" text-anchor="middle">{esc(sub)}</text></g>')
        fig.add(f'<rect class="hl {win(i, t, t + step + 0.2)}" x="{x:.1f}" y="{STAGE_Y}" width="{w:.1f}" '
                f'height="{STAGE_H}" rx="6"/>')
        if mine:
            fig.add(f'<g class="{win(i)}"><rect class="node" x="{x + w - 34:.1f}" y="{STAGE_Y - 9}" width="30" '
                    f'height="16" rx="8"/><text x="{x + w - 19:.1f}" y="{STAGE_Y + 3}" class="s b" '
                    f'text-anchor="middle">mine</text></g>')
        if j < n - 1:
            fig.add(f'<path class="edge {win(i)}" d="M{x + w + 2:.1f} {STAGE_Y + STAGE_H / 2} H{x + w + gap - 2:.1f}" '
                    f'marker-end="url(#arr)"/>')
    fig.add(f'<text x="20" y="{TERM_Y - 8}" class="lbl {win(i)}">A SKETCH OF ONE RUN  (placeholder data)</text>')
    for k, (t, cls, text) in enumerate(term):
        fig.add(f'<text x="34" y="{TERM_Y + 24 + k * 19}" class="code xs {cls} {win(i, t)}" '
                f'xml:space="preserve">{esc(text)}</text>')


fig.add(f'<rect class="term" x="20" y="{TERM_Y}" width="{W - 40}" height="{TERM_H}" rx="6"/>')

# ── 476: pwn.college grades into D2L, no D2L API ─────────────────────────────
scene(0, [
    ("D2L grade page", "console one-liner", True),
    ("enterGrades()", "scrape D2L names", True),
    ("POST /grades/:id", "Rust + axum", True),
    ("load_grades()", "CSV + overrides", True),
    ("match_names()", "fuzzy-match names", True),
    ("fill inputs", "flag gaps", True),
], 1.2, [
    (0.3, "termdim", "// in the D2L console"),
    (0.3, "termt", "eval(await fetch('http://localhost:8192/script').then(r => r.text()))"),
    (1.5, "termt", "enterGrades('module-3')"),
    (2.7, "termdim", "→ POST /grades/module-3  [\"Doe, Student-A 0001\", \"Roe, Student-B 0002\", …]"),
    (3.9, "termdim", "  duplicate dojo accounts: override CSV wins, else keep the best overall"),
    (5.1, "termt", "  \"Doe, Student-A 0001\" → \"student-a doe\" ≈ classlist \"Student-A Doe\"  (SkimMatcherV2)"),
    (6.3, "termt", "← {\"d2l_name\": \"Doe, Student-A 0001\", \"grade\": 0.875}"),
    (6.9, "termok", "  ✓ wrote 87.5 into the D2L input   ·   missing: none   ·   zeros: 1"),
])

# ── 468: autograder releases + my anticheat ──────────────────────────────────
scene(1, [
    ("git push", "student", False),
    ("autograder.yml", "Java 21 + Maven", False),
    ("autograder.py run", "per checkpoint", False),
    ("GitHub release", "results.md", False),
    ("anticheat.yml", "on release: edited", True),
], 1.45, [
    (0.3, "termdim", "$ git push   →   Actions: MSU Autograder"),
    (1.75, "termdim", "release autograder-2026-03-02-14_05_11   (results.md)"),
    (3.2, "termt", "* TokenizerCheckpoint: 100.0% (run:12, failed:0, errors:0, skipped:0)"),
    (3.2, "termt", "* EvalCheckpoint: 75.0% (run:8, failed:4, errors:0, skipped:0)"),
    (4.65, "termdim", "… later, someone edits that release's notes"),
    (6.1, "termerr", "anticheat: saved the edit event as an artifact (kept 90 days)"),
    (6.1, "termerr", "anticheat: opened issue \"Anticheat Report\" [label: anticheat] → instructor"),
    (7.0, "termdim", "the course's autograder; the anticheat workflow is mine"),
])

# ── 366: cached test suites, isolated tests, CSV out ─────────────────────────
scene(2, [
    ("update_testsets()", "cached by release", True),
    ("clone-repos", "per student", False),
    ("cmake + make", "errors → results", False),
    ("gtest --list", "one test at a time", False),
    ("results.json", "+ total", True),
    ("grades.csv", "CSV export", True),
], 1.2, [
    (0.3, "termdim", "$ python grading/grader.py grade --all-students --all-assignments"),
    (0.3, "termt", "testsets: release unchanged since last run, using cache"),
    (2.7, "termdim", "student-a: cmake ✓  make ✓"),
    (3.9, "termt", "  lmsm.Emulator.AddInstruction ......... ok"),
    (3.9, "termerr", "  lmsm.Emulator.StackOverflow .......... timeout (30s), other tests unaffected"),
    (5.1, "termt", "  project: \"(unweighted) 85.42\""),
    (6.3, "termdim", "student,passed,total,grade"),
    (6.3, "termok", "student-a,41,48,0.8541666666666666"),
])

for i, msg in enumerate([
    "476: a script injected into D2L asks a local Rust server for grades, so there's no D2L API and no copy-paste.",
    "468: every push is graded into a release; editing that receipt triggers my anticheat workflow.",
    "366: test suites ship as a release and are cached, and each test runs alone so one hang can't sink the rest.",
]):
    fig.text(20, H - 22, msg, f"cap {win(i, 0, SCENE)}")

fig.write()
