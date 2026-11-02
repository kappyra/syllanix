#!/usr/bin/env python3
"""Synchronize accessible SVG alt text and versioned asset URLs in static HTML.

Source of truth for image descriptions is each Markdown chapter's image alt
field. This script neither rewrites book prose nor uses generic AI captions.
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_IMAGE = re.compile(r"!\[([^\]]+)\]\(\.\./illustrations/(ch-[a-z0-9-]+\.svg)\)")
HTML_IMAGE = re.compile(r'(?P<before><img\s+src="illustrations/(?P<name>ch-[a-z0-9-]+\.svg)"\s+alt=")(?P<alt>[^"]*)(?P<after>")')
ASSETS = ("style.css", "assets/site.js", "assets/theme-boot.js")
VERSION = "20261102-themepack1"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write reviewed patches to HTML")
    args = parser.parse_args()
    descriptions: dict[str, str] = {}
    for chapter in sorted((ROOT / "book/chapters").glob("[0-9][0-9]-*.md")):
        text = chapter.read_text(encoding="utf-8")
        for alt, name in MARKDOWN_IMAGE.findall(text):
            normalized = re.sub(r"\s+", " ", alt).strip()
            if not normalized:
                raise AssertionError(f"{chapter}: empty Markdown alt for {name}")
            if name in descriptions and descriptions[name] != normalized:
                raise AssertionError(f"conflicting image descriptions for {name}")
            descriptions[name] = normalized

    replaced = 0
    modified = []
    for page in sorted(ROOT.glob("*.html")):
        original = page.read_text(encoding="utf-8")
        missing = set()
        def image_replace(match: re.Match[str]) -> str:
            nonlocal replaced
            name = match.group("name")
            if name not in descriptions:
                missing.add(name)
                return match.group(0)
            expected = html.escape(descriptions[name], quote=True)
            if match.group("alt") == expected:
                return match.group(0)
            replaced += 1
            return match.group("before") + expected + match.group("after")
        updated = HTML_IMAGE.sub(image_replace, original)
        if missing:
            raise AssertionError(f"{page.name}: no source alt for {sorted(missing)}")
        for name in ASSETS:
            updated = re.sub(
                r'(?P<prefix>\b(?:src|href)=")' + re.escape(name) + r'(?:\?v=[^"]+)?(?P<end>")',
                lambda match: match.group("prefix") + name + "?v=" + VERSION + match.group("end"),
                updated
            )
        if updated != original:
            modified.append(page.name)
            if args.write:
                page.write_text(updated, encoding="utf-8")
    print(f"Figures with source descriptions={len(descriptions)}; updated alt attributes={replaced}; HTML pages changed={len(modified)}; mode={'WRITE' if args.write else 'DRY-RUN'}")
    if len(descriptions) != 109:
        raise AssertionError(f"Expected 109 original figure descriptions, found {len(descriptions)}")
    if not args.write and modified:
        print("Run with --write to synchronize public HTML. First pages: " + ", ".join(modified[:10]))


if __name__ == "__main__":
    main()
