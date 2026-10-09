#!/usr/bin/env python3
"""
Turn a learn-this report draft into one self-contained HTML file.

Usage:
    python3 finalize_report.py draft.html final.html

The draft is written against local files so it stays small while you work:
    <link rel="stylesheet" href="report.css">
    <script src="report.js"></script>
    <img src="frames/frame_0324.jpg" alt="...">

This script inlines all of them (stylesheet -> <style>, script -> inline
<script>, local images -> data: URIs), so the result opens anywhere with no
sibling files. report.css and report.js are looked up next to the draft first,
then in the skill's assets/ folder, so you never need to copy them.

Fails loudly if a referenced local file is missing, rather than shipping a
report with broken images. http(s) and data: URLs are left alone.
"""
import base64
import mimetypes
import os
import re
import sys

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def is_local(ref: str) -> bool:
    return not re.match(r"^(https?:|data:|//|#|mailto:)", ref.strip(), re.I)


def find(ref: str, base: str) -> str:
    ref = ref.split("?")[0].split("#")[0]
    for root in (base, ASSETS):
        path = os.path.normpath(os.path.join(root, ref))
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(f"referenced file not found: {ref} (looked in {base} and {os.path.normpath(ASSETS)})")


def data_uri(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode('ascii')}"


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    src, dest = sys.argv[1], sys.argv[2]
    base = os.path.dirname(os.path.abspath(src))
    with open(src, encoding="utf-8") as f:
        html = f.read()

    def css(m):
        tag = m.group(0)
        href = re.search(r'href="([^"]+)"', tag)
        if "stylesheet" not in tag or not href or not is_local(href.group(1)):
            return tag
        with open(find(href.group(1), base), encoding="utf-8") as f:
            return f"<style>\n{f.read()}\n</style>"

    def js(m):
        src_ref = m.group(1)
        if not is_local(src_ref):
            return m.group(0)
        with open(find(src_ref, base), encoding="utf-8") as f:
            return f"<script>\n{f.read()}\n</script>"

    def img(m):
        ref = m.group(2)
        if not is_local(ref):
            return m.group(0)
        return f'{m.group(1)}{data_uri(find(ref, base))}{m.group(3)}'

    try:
        html = re.sub(r"<link\b[^>]*>", css, html)
        html = re.sub(r'<script\b[^>]*\bsrc="([^"]+)"[^>]*>\s*</script>', js, html)
        html = re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)(")', img, html)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    visible = re.sub(r"<!--.*?-->|<style\b.*?</style>|<script\b.*?</script>", "", html, flags=re.S)
    leftovers = re.findall(r'(?:src|href)="((?!https?:|data:|#|mailto:|//)[^"]+)"', visible)
    if leftovers:
        print("WARNING: local references left un-inlined: " + ", ".join(sorted(set(leftovers))), file=sys.stderr)

    with open(dest, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {dest} ({os.path.getsize(dest) / 1024:.0f} KB, self-contained)")


if __name__ == "__main__":
    main()
