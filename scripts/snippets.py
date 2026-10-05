#!/usr/bin/env python3
"""Build the code-snippet carousel for the profile README.

Reads scripts/snippets.json, fetches each excerpt from GitHub at a pinned
commit, and writes:
  assets/snippets.svg  - auto-advancing slideshow shown in the README
  docs/snippets.json   - highlighted snippets for the interactive carousel

"repo" is "name" (the configured user's) or "owner/name". On first run a
snippet is pinned to its repo's current HEAD ("ref") and the excerpt is cached
in the config ("code"), so line ranges never drift and later runs need no
access to private repos. Snippets marked "private" get no source link.
Requires pygments.
"""
import json
import os
import re
import textwrap
import urllib.request
from html import escape
from pathlib import Path

from pygments import lex
from pygments.lexers import get_lexer_for_filename
from pygments.token import Comment, Keyword, Literal, Name, Number, Operator, String

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "scripts" / "snippets.json"

SECONDS_PER_SLIDE = 9
MAX_COLS = 92
WIDTH = 780
LINE_H = 19
PAD = 20
HEADER_H = 58

# Token class -> (light, dark). Shared by the SVG and the Pages carousel.
THEME = {
    "k": ("#cf222e", "#ff7b72"),
    "f": ("#8250df", "#d2a8ff"),
    "t": ("#953800", "#ffa657"),
    "s": ("#0a3069", "#a5d6ff"),
    "n": ("#0550ae", "#79c0ff"),
    "c": ("#6e7781", "#8b949e"),
}


def token_class(ttype):
    if ttype in Literal.Scalar.Plain:
        return ""
    if ttype in Comment:
        return "c"
    if ttype in String:
        return "s"
    if ttype in Number or ttype in Name.Constant or ttype in Keyword.Constant:
        return "n"
    if ttype in Keyword.Type or ttype in Name.Class or ttype in Name.Builtin:
        return "t"
    if ttype in Keyword or ttype in Operator.Word:
        return "k"
    if ttype in Name.Function or ttype in Name.Decorator or ttype in Name.Function.Magic:
        return "f"
    if ttype in Literal or ttype in Name.Tag:
        return "n"
    return ""


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def highlight(code, path):
    """Return a list of lines, each a list of (class, text) runs."""
    lexer = get_lexer_for_filename(path, stripnl=False, ensurenl=False)

    def tokens(text):
        directive = False
        for ttype, value in lex(text, lexer):
            if ttype not in Comment.Preproc:
                yield ttype, value
                continue
            # C lexers tag a whole macro body as a preprocessor comment; colour it as code.
            if value == "#":
                directive = True
                yield Keyword, value
                continue
            if directive:
                word = value.split(" ", 1)
                yield Keyword, word[0]
                value = " " + word[1] if len(word) > 1 else ""
                directive = False
            yield from lex(value, lexer)

    lines = [[]]
    for ttype, value in tokens(code):
        cls = token_class(ttype)
        for i, part in enumerate(value.split("\n")):
            if i:
                lines.append([])
            if part:
                lines[-1].append((cls, part))
    return lines


def truncate(runs, limit):
    out, used = [], 0
    for cls, text in runs:
        if used + len(text) > limit:
            out.append((cls, text[: limit - used - 1] + "…"))
            break
        out.append((cls, text))
        used += len(text)
    return out


def fetch(snippet, full):
    if "code" in snippet:
        return snippet["code"]
    if not snippet.get("ref"):
        snippet["ref"] = get(f"https://api.github.com/repos/{full}/commits?per_page=1")[0]["sha"]
    req = urllib.request.Request(
        f"https://api.github.com/repos/{full}/contents/{snippet['path']}?ref={snippet['ref']}",
        headers={"Accept": "application/vnd.github.raw"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        source = resp.read().decode()
    start, end = snippet["lines"]
    code = "\n".join(source.expandtabs(4).split("\n")[start - 1 : end])
    snippet["code"] = textwrap.dedent(code).strip("\n")
    return snippet["code"]


def css():
    light = "\n".join(f"  .{k} {{ fill: {v[0]}; color: {v[0]}; }}" for k, v in THEME.items())
    dark = "\n".join(f"    .{k} {{ fill: {v[1]}; color: {v[1]}; }}" for k, v in THEME.items())
    return light, dark


def render_svg(slides):
    n = len(slides)
    max_lines = max(len(s["lines"]) for s in slides)
    code_top = PAD + HEADER_H
    height = code_top + max_lines * LINE_H + PAD + 22
    period = n * SECONDS_PER_SLIDE
    share = 100 / n
    fade = min(3.0, share / 6)
    # Shift every slide by the fade-in time so the first one is fully visible at load.
    offset = fade / 100 * period
    light, dark = css()

    body = []
    for i, s in enumerate(slides):
        g = [f'<g class="sl" style="animation-delay:{i * SECONDS_PER_SLIDE - offset:.2f}s">']
        g.append(f'<text x="{PAD}" y="{PAD + 14}" class="h">{escape(s["title"])}</text>')
        g.append(f'<text x="{PAD}" y="{PAD + 34}" class="m">{escape(s["repo"])} · {escape(s["path"])}</text>')
        for j, runs in enumerate(s["lines"]):
            y = code_top + (j + 1) * LINE_H - 5
            spans = "".join(
                f'<tspan class="{cls}">{escape(text)}</tspan>' if cls else escape(text)
                for cls, text in truncate(runs, MAX_COLS)
            )
            g.append(f'<text x="{PAD}" y="{y}" class="code" xml:space="preserve">{spans}</text>')
        g.append("</g>")
        body.append("\n".join(g))

    dots_y = height - PAD + 2
    dots_x0 = WIDTH / 2 - (n - 1) * 8
    for i in range(n):
        body.append(f'<circle cx="{dots_x0 + i * 16:.1f}" cy="{dots_y}" r="3.5" class="dot"/>'
                    f'<circle cx="{dots_x0 + i * 16:.1f}" cy="{dots_y}" r="3.5" class="dot on" '
                    f'style="animation-delay:{i * SECONDS_PER_SLIDE - offset:.2f}s"/>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">
<style>
  .card {{ fill: #f6f8fa; stroke: #d1d9e0; }}
  text {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; font-size: 13px; fill: #1f2328; }}
  .h {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 15px; font-weight: 600; }}
  .m {{ font-size: 12px; fill: #59636e; }}
  .dot {{ fill: #d1d9e0; }}
  .on {{ fill: #59636e; }}
{light}
  .sl, .on {{ opacity: 0; animation: cycle {period}s infinite both; }}
  @keyframes cycle {{
    0% {{ opacity: 0; }}
    {fade:.2f}% {{ opacity: 1; }}
    {share - fade:.2f}% {{ opacity: 1; }}
    {share:.2f}% {{ opacity: 0; }}
    100% {{ opacity: 0; }}
  }}
  @media (prefers-color-scheme: dark) {{
    .card {{ fill: #151b23; stroke: #3d444d; }}
    text {{ fill: #e6edf3; }}
    .m {{ fill: #9198a1; }}
    .dot {{ fill: #3d444d; }}
    .on {{ fill: #9198a1; }}
{dark}
  }}
  @media (prefers-reduced-motion: reduce) {{
    .sl, .on {{ animation: none; }}
    .sl:first-of-type, .on:nth-of-type(2) {{ opacity: 1; }}
  }}
</style>
<rect class="card" x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8"/>
{chr(10).join(body)}
</svg>
"""


def to_html(lines):
    return "\n".join(
        "".join(f'<span class="{cls}">{escape(t)}</span>' if cls else escape(t) for cls, t in runs)
        for runs in lines
    )


def main():
    config = json.loads(CONFIG_PATH.read_text())
    user = config["user"]
    slides = []
    for snippet in config["snippets"]:
        full = snippet["repo"] if "/" in snippet["repo"] else f"{user}/{snippet['repo']}"
        code = fetch(snippet, full)
        start, end = snippet["lines"]
        slides.append({
            **{k: snippet[k] for k in ("path", "title", "caption")},
            "repo": snippet["repo"],
            "url": None if snippet.get("private") else
                f"https://github.com/{full}/blob/{snippet['ref']}/{snippet['path']}#L{start}-L{end}",
            "lines": highlight(code, snippet["path"]),
        })

    text = json.dumps(config, indent=2, ensure_ascii=False) + "\n"
    text = re.sub(r"\[\s+(\d+),\s+(\d+)\s+\]", r"[\1, \2]", text)
    CONFIG_PATH.write_text(text)
    (ROOT / "assets" / "snippets.svg").write_text(render_svg(slides))
    (ROOT / "docs" / "snippets.json").write_text(json.dumps({
        "theme": THEME,
        "snippets": [{**{k: v for k, v in s.items() if k != "lines"}, "html": to_html(s["lines"])} for s in slides],
    }, indent=1) + "\n")
    print(f"{len(slides)} snippets")


if __name__ == "__main__":
    main()
