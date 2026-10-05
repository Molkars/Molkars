#!/usr/bin/env python3
"""Build every animated figure, and optionally preview them locally.

    python3 scripts/figures/build.py            # rebuild assets/figures/*.svg
    python3 scripts/figures/build.py --preview  # rebuild, then open a gallery in your browser

Each figure lives in its own script in this directory (anything that isn't
build.py, common.py or gif.py). The gallery is written to assets/figures/preview.html,
which is git-ignored.
"""
import runpy
import sys
import webbrowser
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import OUT_DIR, ROOT  # noqa: E402


def build():
    for script in sorted(HERE.glob("*.py")):
        if script.name not in ("build.py", "common.py", "gif.py"):
            runpy.run_path(str(script), run_name="__main__")


def preview():
    figures = sorted(OUT_DIR.glob("*.svg"))
    cards = "\n".join(f"""
  <section>
    <header><h2>{escape(f.stem)}</h2><button onclick="replay(this)">Replay</button></header>
    <img src="{escape(f.name)}" alt="{escape(f.stem)}">
  </section>""" for f in figures)
    page = OUT_DIR / "preview.html"
    page.write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Figure Preview</title>
<style>
  :root {{ color-scheme: light dark; --bg: #ffffff; --fg: #1f2328; --line: #d1d9e0; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg: #0d1117; --fg: #e6edf3; --line: #3d444d; }} }}
  body {{ margin: 0; background: var(--bg); color: var(--fg); font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }}
  main {{ max-width: 820px; margin: 0 auto; padding: 24px 16px 64px; }}
  section {{ margin-bottom: 40px; }}
  header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }}
  h2 {{ font-size: 15px; margin: 0; }}
  button {{ font: inherit; border: 1px solid var(--line); background: transparent; color: var(--fg); border-radius: 6px; padding: 2px 10px; cursor: pointer; }}
  img {{ max-width: 100%; height: auto; display: block; }}
  p {{ color: #8b949e; }}
</style>
</head>
<body>
<main>
  <p>Local preview of the README figures. Your OS light/dark setting picks the theme. Rebuild with <code>python3 scripts/figures/build.py --preview</code>.</p>
{cards}
</main>
<script>
  function replay(button) {{
    const img = button.closest("section").querySelector("img");
    img.src = img.src.split("?")[0] + "?" + Date.now();
  }}
</script>
</body>
</html>
""")
    print(f"preview: {page.relative_to(ROOT)}")
    webbrowser.open(page.as_uri())


if __name__ == "__main__":
    build()
    if "--preview" in sys.argv:
        preview()
