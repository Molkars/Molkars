#!/usr/bin/env python3
"""Build language stats for the profile README.

Writes:
  assets/languages.svg  - static bar shown in the README
  docs/data.json        - per-repo breakdown for the interactive page

Uses only the standard library. Set GITHUB_TOKEN to avoid rate limits.
"""
import json
import os
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "scripts" / "config.json").read_text())

COLORS = {
    "Rust": "#dea584", "Java": "#b07219", "Dart": "#00b4ab", "C": "#555555",
    "C++": "#f34b7d", "Kotlin": "#a97bff", "Python": "#3572a5",
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Ruby": "#701516",
    "Swift": "#f05138", "Objective-C": "#438eff", "Lean": "#6e7681",
    "Go": "#00add8", "Zig": "#ec915c", "Haskell": "#5e5086",
}
OTHER_COLOR = "#8b949e"


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def list_repos(user):
    repos, page = [], 1
    while True:
        batch = get(f"https://api.github.com/users/{user}/repos?type=owner&per_page=100&page={page}")
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


def collect():
    skip_repos = set(CONFIG["skip_repos"])
    skip_langs = set(CONFIG["skip_languages"])
    out = []
    for repo in list_repos(CONFIG["user"]):
        if repo["name"] in skip_repos or (repo["fork"] and not CONFIG["include_forks"]):
            continue
        override = CONFIG["repo_overrides"].get(repo["name"], {})
        skip = skip_langs | set(override.get("skip_languages", []))
        langs = {k: v for k, v in get(repo["languages_url"]).items() if k not in skip}
        if not langs:
            continue
        out.append({
            "name": repo["name"],
            "url": repo["html_url"],
            "description": repo["description"] or "",
            "pushed_at": repo["pushed_at"],
            "languages": dict(sorted(langs.items(), key=lambda kv: -kv[1])),
            "note": override.get("note", ""),
        })
    return sorted(out, key=lambda r: -sum(r["languages"].values()))


def totals(repos):
    acc = {}
    for repo in repos:
        for lang, n in repo["languages"].items():
            acc[lang] = acc.get(lang, 0) + n
    return dict(sorted(acc.items(), key=lambda kv: -kv[1]))


def render_svg(total):
    top_n = CONFIG["top_n"]
    items = list(total.items())
    if len(items) > top_n:
        items = items[: top_n - 1] + [("Other", sum(n for _, n in items[top_n - 1 :]))]
    grand = sum(n for _, n in items)

    width, bar_y, bar_h = 480, 16, 10
    row_h, col_w = 22, width / 2
    rows = (len(items) + 1) // 2
    height = bar_y + bar_h + 20 + rows * row_h

    parts = [f'<clipPath id="r"><rect x="0" y="{bar_y}" width="{width}" height="{bar_h}" rx="5"/></clipPath>',
             '<g clip-path="url(#r)">']
    x = 0.0
    for lang, n in items:
        w = n / grand * width
        color = COLORS.get(lang, OTHER_COLOR)
        parts.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{w:.2f}" height="{bar_h}" fill="{color}"/>')
        x += w
    parts.append("</g>")

    for i, (lang, n) in enumerate(items):
        col, row = i % 2, i // 2
        cx = col * col_w + 6
        cy = bar_y + bar_h + 26 + row * row_h
        color = COLORS.get(lang, OTHER_COLOR)
        parts.append(f'<circle cx="{cx}" cy="{cy - 4}" r="5" fill="{color}"/>')
        parts.append(f'<text x="{cx + 14}" y="{cy}" class="l">{escape(lang)}</text>')
        parts.append(f'<text x="{cx + col_w - 26}" y="{cy}" class="p" text-anchor="end">{n / grand * 100:.1f}%</text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
  text {{ font: 13px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: #1f2328; }}
  .p {{ fill: #59636e; font-variant-numeric: tabular-nums; }}
  @media (prefers-color-scheme: dark) {{
    text {{ fill: #e6edf3; }}
    .p {{ fill: #9198a1; }}
  }}
</style>
{chr(10).join(parts)}
</svg>
"""


def main():
    repos = collect()
    total = totals(repos)
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "docs" / "data.json").write_text(json.dumps({
        "user": CONFIG["user"],
        "colors": COLORS,
        "totals": total,
        "repos": repos,
    }, indent=1) + "\n")
    (ROOT / "assets" / "languages.svg").write_text(render_svg(total))
    print(f"{len(repos)} repos; " + ", ".join(f"{k} {v}" for k, v in list(total.items())[:6]))


if __name__ == "__main__":
    main()
