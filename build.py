#!/usr/bin/env python3
"""Build the cellar site from wines.json + photos/ into two self-contained pages.

    dist/index.html     full standalone document, openable locally
    dist/artifact.html  body-only version for the Artifact tool (it supplies the shell)

Photos are base64-embedded so both files work with no network access.
Stdlib only — no install step.
"""

import base64
import json
import mimetypes
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
DOCS = ROOT / "docs"
MAX_PHOTO_BYTES = 400_000  # a resized bottle shot; larger means sips wasn't run


def load_wines():
    data = json.loads((ROOT / "wines.json").read_text(encoding="utf-8"))
    wines = data.get("wines", [])
    seen = set()
    for w in wines:
        wid = w.get("id")
        if not wid:
            sys.exit(f"error: a wine entry has no id: {w.get('name', '?')}")
        if wid in seen:
            sys.exit(f"error: duplicate id {wid!r}")
        seen.add(wid)
    return data, wines


def embed_photos(wines):
    """Read each wine's photo into a data URI keyed by wine id."""
    photos = {}
    for w in wines:
        rel = w.get("photo")
        if not rel:
            continue
        path = ROOT / rel
        if not path.exists():
            print(f"  ! {w['id']}: photo not found at {rel} — using the bottle glyph")
            continue
        raw = path.read_bytes()
        if len(raw) > MAX_PHOTO_BYTES:
            print(f"  ! {w['id']}: {len(raw) // 1024}KB is large — "
                  f"run: sips -Z 600 {rel}")
        mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        photos[w["id"]] = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
    return photos


def as_js(obj):
    """JSON safe to drop inside a <script> block."""
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")


def main():
    data, wines = load_wines()
    print(f"cellar: {len(wines)} entries")

    photos = embed_photos(wines)
    built = datetime.now().strftime("%-d %B %Y · %H:%M")

    body = (ROOT / "template.html").read_text(encoding="utf-8")
    for marker, value in (
        ("/*__WINES__*/{ wines: [] }", as_js(data)),
        ("/*__PHOTOS__*/{}", as_js(photos)),
        ("/*__BUILT__*/", built),
    ):
        if marker not in body:
            sys.exit(f"error: template is missing the {marker!r} placeholder")
        body = body.replace(marker, value, 1)

    DIST.mkdir(exist_ok=True)
    DOCS.mkdir(exist_ok=True)
    (DIST / "artifact.html").write_text(body, encoding="utf-8")

    # Standalone: lift <title> out of the body and wrap in a real document.
    title_match = re.search(r"<title>(.*?)</title>\s*", body, re.S)
    title = title_match.group(1) if title_match else "The Cellar"
    stripped = body.replace(title_match.group(0), "", 1) if title_match else body
    standalone = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{title}</title>\n"
        "<link rel=\"icon\" href=\"data:image/svg+xml,"
        "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
        "%3Ctext y='.9em' font-size='90'%3E%F0%9F%8D%B7%3C/text%3E%3C/svg%3E\">\n"
        "</head>\n<body>\n" + stripped + "\n</body>\n</html>\n"
    )
    (DIST / "index.html").write_text(standalone, encoding="utf-8")
    (DOCS / "index.html").write_text(standalone, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    cellar = [w for w in wines if w.get("status") != "consumed"]
    kb = len(standalone.encode()) // 1024
    print(f"  {len(cellar)} in cellar, {len(wines) - len(cellar)} in history, "
          f"{len(photos)} photo(s) embedded")
    print(f"built dist/index.html, dist/artifact.html and docs/index.html ({kb}KB)")


if __name__ == "__main__":
    main()
