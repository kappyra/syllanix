#!/usr/bin/env python3
"""Independent, bounded content/SVG checks for Syllanix chapter 6.

The published repository does not ship the private Syllanix build harness.
This script verifies the published Markdown, exercises, static HTML and SVGs
without relying on that harness. It only executes explicitly marked snippets
from this chapter and its answers, each in a restricted subprocess.
"""
from __future__ import annotations

import ast
import html.parser
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "book/chapters/06-loops.md"
SOLUTIONS = ROOT / "book/solutions/06-loops.md"
SITE = ROOT / "ch-06-loops.html"
SVG_NAMES = ("ch-06-loop-flow.svg", "ch-06-break-continue.svg")

BLOCK = re.compile(
    r"^\x60{3}python exec(?P<error> expect-error)?\n(?P<source>.*?)^\x60{3}\s*\n"
    r"^\x60{3}output\n(?P<output>.*?)^\x60{3}",
    re.MULTILINE | re.DOTALL,
)
START = re.compile(r"^\x60{3}python exec(?: expect-error)?$", re.MULTILINE)
OUTPUT = re.compile(r"^\x60{3}output$", re.MULTILINE)
EXERCISE = re.compile(r"^### (\d+)\. ", re.MULTILINE)
SOL_HEADING = re.compile(r"^## (\d+)\. ", re.MULTILINE)
NS = "{http://www.w3.org/2000/svg}"
UNSAFE_TAGS = {"script", "foreignObject", "image", "iframe", "use"}
UNSAFE_NAMES = {"eval", "exec", "compile", "open", "input", "__import__"}
EXPECTED_EXERCISES = 13


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def parse_and_run(label: str, doc: str) -> int:
    matches = list(BLOCK.finditer(doc))
    require(len(matches) == len(START.findall(doc)), f"{label}: unpaired Python exec block")
    require(len(matches) == len(OUTPUT.findall(doc)), f"{label}: unpaired output block")
    for n, m in enumerate(matches, 1):
        source, expected = m.group("source"), m.group("output").strip()
        tree = ast.parse(source, filename=f"{label}:example-{n}")
        for node in ast.walk(tree):
            require(
                not isinstance(node, (ast.Import, ast.ImportFrom)),
                f"{label}:example-{n}: import is not supported in this bounded check",
            )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                require(node.func.id not in UNSAFE_NAMES, f"{label}:example-{n}: unsupported call {node.func.id}")
        # No shell, isolated interpreter, temporary working directory, 3-second cap.
        with tempfile.TemporaryDirectory(prefix="syllanix-ch06-") as temp:
            try:
                result = subprocess.run(
                    [sys.executable, "-I", "-S", "-B", "-c", source],
                    cwd=temp,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=3,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise AssertionError(f"{label}:example-{n} exceeded 3 seconds") from exc
        if m.group("error"):
            require(result.returncode != 0, f"{label}:example-{n}: expected error, got success")
            require(expected in result.stderr, f"{label}:example-{n}: unexpected error: {result.stderr[-400:]}")
        else:
            require(result.returncode == 0, f"{label}:example-{n}: failed: {result.stderr[-400:]}")
            require(result.stdout.strip() == expected, f"{label}:example-{n}: output mismatch: {result.stdout!r} != {expected!r}")
    return len(matches)


class SiteChecker(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.svg_images: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"] or "")
        if tag == "img" and "ch-06-" in (a.get("src") or ""):
            self.svg_images.append((a.get("src") or "", a.get("alt") or ""))


def check_svg() -> None:
    for name in SVG_NAMES:
        book = (ROOT / "book/illustrations" / name).read_bytes()
        site = (ROOT / "illustrations" / name).read_bytes()
        require(book == site, f"{name}: Markdown/Site SVG copies differ")
        root = ET.fromstring(book)
        require(root.tag == NS + "svg", f"{name}: root is not SVG")
        require(root.get("viewBox") is not None, f"{name}: viewBox missing")
        require(root.get("role") == "img", f"{name}: accessibility role missing")
        label = root.get("aria-labelledby", "").split()
        children_by_id = {element.get("id"): element for element in root.iter() if element.get("id")}
        require(len(label) >= 2 and all(key in children_by_id for key in label), f"{name}: aria-labelledby broken")
        require(root.find(NS + "title") is not None and root.find(NS + "desc") is not None, f"{name}: accessible title or description missing")
        for element in root.iter():
            local = element.tag.split("}")[-1]
            require(local not in UNSAFE_TAGS, f"{name}: unsafe element {local}")
            for attr in element.attrib:
                local_attr = attr.split("}")[-1].lower()
                require(local_attr not in {"href", "onload", "onclick", "onerror"}, f"{name}: unsafe attribute {attr}")
        text_count = sum(1 for e in root.iter() if e.tag == NS + "text")
        require(text_count >= 10, f"{name}: unexpectedly few diagram labels")


def main() -> None:
    chapter = CHAPTER.read_text(encoding="utf-8")
    solutions = SOLUTIONS.read_text(encoding="utf-8")
    require("exercise_count: 13" in chapter and "exercise_count: 13" in solutions, "exercise metadata count mismatch")
    require([int(n) for n in EXERCISE.findall(chapter)] == list(range(1, 14)), "chapter exercises must be numbered 1 to 13")
    require([int(n) for n in SOL_HEADING.findall(solutions)] == list(range(1, 14)), "solutions must match exercises 1 to 13")
    a, b = parse_and_run("chapter", chapter), parse_and_run("solutions", solutions)
    check_svg()
    html = SITE.read_text(encoding="utf-8")
    parsed = SiteChecker()
    parsed.feed(html)
    require(all(parsed.ids.count(f"ex-ch06-{i:02d}") == 1 for i in range(1, 14)), "HTML exercise IDs incomplete or duplicated")
    require(len(parsed.svg_images) == 2 and all(alt for _, alt in parsed.svg_images), "HTML SVG images need meaningful alt")
    require("внешнего цикла" in html and "неограниченным" in html, "HTML missing corrected explanation")
    print(f"PASS: {a} chapter examples, {b} solution examples, 13 exercises, 2 synchronized accessible SVG diagrams and published HTML")


if __name__ == "__main__":
    main()
