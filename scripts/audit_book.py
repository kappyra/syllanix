#!/usr/bin/env python3
"""Read-only Syllanix audit for all chapters, solutions, HTML and SVG.

No book examples are executed: the script parses their syntax only. Actual
execution requires a separately sandboxed, version-specific verification pass.
"""
from __future__ import annotations

import ast
import html.parser
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "book/chapters"
SOLUTIONS = ROOT / "book/solutions"
FIGURES = ROOT / "book/illustrations"
PUBLISHED_FIGURES = ROOT / "illustrations"
HEAD = re.compile(r"^---\n(.*?)\n---\n", re.S)
FENCE = re.compile(r"^(`{3,})(.*?)$", re.M)
EXERCISE = re.compile(r"^###\s+(\d+)\.\s+", re.M)
SOLUTION = re.compile(r"^##\s+(\d+)\.\s+", re.M)
CODE_BLOCK = re.compile(r"^`{3}python exec(?: expect-error)?\n(.*?)^`{3}", re.M | re.S)
OUT_BLOCK = re.compile(r"^`{3}output\n(.*?)^`{3}", re.M | re.S)
MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^\s)]+)(?:\s+[^)]*)?\)")
SVG = "{http://www.w3.org/2000/svg}"
BAD_SVG_TAGS = {"script", "foreignObject", "image", "iframe"}
BAD_SVG_ATTR = {"onload", "onclick", "onerror"}
MAX_FAILS = 70


class Page(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.illustrations: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if attr.get("id"):
            self.ids.append(attr["id"] or "")
        if tag == "img" and "/ch-" in ("/" + (attr.get("src") or "")):
            self.illustrations.append((attr.get("src") or "", attr.get("alt") or ""))


def main() -> int:
    findings: list[tuple[str, str]] = []
    stats: list[tuple] = []

    def finding(level: str, text: str) -> None:
        findings.append((level, text))

    chapters = sorted(CHAPTERS.glob("[0-9][0-9]-*.md"))
    require_count = 56
    if len(chapters) != require_count:
        finding("ERROR", f"Expected {require_count} chapters, got {len(chapters)}")

    md = {}
    total_exec = total_ex = total_ill = total_solution = 0
    for ch in chapters:
        doc = ch.read_text(encoding="utf-8")
        number = int(ch.name[:2])
        fm = HEAD.search(doc)
        if not fm:
            finding("ERROR", f"{ch}: YAML frontmatter missing")
            continue
        head = fm.group(1)
        count = re.search(r"(?m)^exercise_count:\s*(\d+)\s*$", head)
        want = int(count.group(1)) if count else -1
        exercises = [int(x) for x in EXERCISE.findall(doc)]
        if want != len(exercises) or exercises != list(range(1, want + 1)):
            finding("ERROR", f"ch {number:02d}: exercise_count={want} but exercise headings={exercises}")
        solution = SOLUTIONS / ch.name
        if not solution.exists():
            finding("ERROR", f"ch {number:02d}: solution file missing")
            sol_exercises = []
        else:
            sol = solution.read_text(encoding="utf-8")
            smeta = HEAD.search(sol)
            s_count = re.search(r"(?m)^exercise_count:\s*(\d+)\s*$", smeta.group(1)) if smeta else None
            sol_exercises = [int(x) for x in SOLUTION.findall(sol)]
            if sol_exercises != exercises or not s_count or int(s_count.group(1)) != want:
                finding("ERROR", f"ch {number:02d}: solutions do not match exercises")
            if len(CODE_BLOCK.findall(sol)) != len(OUT_BLOCK.findall(sol)):
                finding("WARN", f"ch {number:02d}: solution code/output counts differ")
            total_solution += len(CODE_BLOCK.findall(sol))
        if len(CODE_BLOCK.findall(doc)) != len(OUT_BLOCK.findall(doc)):
            finding("WARN", f"ch {number:02d}: runnable code/output counts differ")
        for idx, code in enumerate(CODE_BLOCK.findall(doc), start=1):
            try:
                ast.parse(code)
            except SyntaxError as exc:
                # Examples marked 'expect-error' may deliberately contain bad syntax.
                # Those are still recorded for manual confirmation.
                finding("REVIEW", f"ch {number:02d} example {idx}: SyntaxError at line {exc.lineno}")
        images = MD_IMAGE.findall(doc)
        for alt, link in images:
            target = (ch.parent / link).resolve()
            if not target.is_file():
                finding("ERROR", f"ch {number:02d}: illustration missing {link}")
            if not alt.strip():
                finding("WARN", f"ch {number:02d}: Markdown figure lacks descriptive alt {link}")
        html_file = ROOT / ("ch-" + ch.name.replace(".md", ".html"))
        if not html_file.is_file():
            finding("ERROR", f"ch {number:02d}: HTML page missing")
        else:
            page = Page()
            page.feed(html_file.read_text(encoding="utf-8"))
            ids = [f"ex-ch{number:02d}-{i:02d}" for i in range(1, want + 1)]
            if any(page.ids.count(x) != 1 for x in ids):
                finding("WARN", f"ch {number:02d}: HTML exercise IDs do not match Markdown")
            for src, alt in page.illustrations:
                if not (ROOT / src).is_file():
                    finding("ERROR", f"ch {number:02d}: site image missing {src}")
                if not alt.strip():
                    finding("WARN", f"ch {number:02d}: HTML SVG empty alt {src}")
        total_exec += len(CODE_BLOCK.findall(doc))
        total_ex += len(exercises)
        total_ill += len(images)
        stats.append((number, len(doc), len(CODE_BLOCK.findall(doc)), len(exercises), len(images)))
        md[number] = doc

    svgs = list(FIGURES.glob("*.svg"))
    for source in svgs:
        copy = PUBLISHED_FIGURES / source.name
        if not copy.is_file():
            finding("ERROR", f"{source.name}: site SVG copy missing")
            continue
        if source.read_bytes() != copy.read_bytes():
            finding("ERROR", f"{source.name}: source and published SVG differ")
        try:
            root = ET.parse(source).getroot()
            if root.tag != SVG + "svg" or not root.get("viewBox"):
                finding("ERROR", f"{source.name}: invalid SVG root/viewBox")
            titles = root.findall(SVG + "title")
            descs = root.findall(SVG + "desc")
            if not titles or not descs:
                finding("WARN", f"{source.name}: missing accessible title/desc")
            for el in root.iter():
                if el.tag.split("}")[-1] in BAD_SVG_TAGS:
                    finding("ERROR", f"{source.name}: active/external SVG node")
                for key in el.attrib:
                    if key.split("}")[-1].lower() in BAD_SVG_ATTR:
                        finding("ERROR", f"{source.name}: event handler in SVG")
        except ET.ParseError as exc:
            finding("ERROR", f"{source.name}: invalid XML: {exc}")

    print("SYLLANIX WHOLE-BOOK AUDIT")
    print(f"chapters={len(chapters)} exercises={total_ex} runnable_samples={total_exec} solution_samples={total_solution} figure_references={total_ill} source_svgs={len(svgs)}")
    for n, chars, examples, exercises, pictures in stats:
        print(f"CH {n:02d}  chars={chars:5d} examples={examples:2d} exercises={exercises:2d} figures={pictures}")
    counts = Counter(level for level, _ in findings)
    print("FINDINGS", dict(counts))
    for level, message in findings[:MAX_FAILS]:
        print(f"{level}: {message}")
    if len(findings) > MAX_FAILS:
        print(f"... {len(findings) - MAX_FAILS} additional findings; see source code for full checks.")
    errors = counts["ERROR"]
    print(f"RESULT: {'FAIL' if errors else 'PASS'} (fatal errors={errors}; review flags are not proof of inaccuracy)")
    return int(errors > 0)


if __name__ == "__main__":
    sys.exit(main())
