#!/usr/bin/env python3
"""Conservative execution smoke test for self-contained, side-effect-free examples.

This is NOT a general sandbox and makes no claim to verify all examples.
GitHub Actions runs it with read-only repository permissions and isolated
subprocesses; imports, I/O, and unrecognized calls are deliberately skipped.
"""
from __future__ import annotations
import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r"^`{3}python exec\n(.*?)^`{3}\n\s*^`{3}output\n(.*?)^`{3}", re.M | re.S)
PURE_BUILTINS = {"print", "range", "len", "int", "float", "str", "bool",
                 "list", "tuple", "dict", "set", "sum", "min", "max",
                 "abs", "round", "sorted", "enumerate", "zip", "all", "any", "type"}
BANNED_NODES = (ast.Import, ast.ImportFrom, ast.With, ast.AsyncWith,
                ast.AsyncFunctionDef, ast.Await, ast.Global, ast.Nonlocal,
                ast.ClassDef, ast.Raise, ast.Try, ast.TryStar,
                ast.Delete, ast.Yield, ast.YieldFrom, ast.NamedExpr)
PURE_CODE = {"True", "False", "None"}


def is_pure(tree: ast.AST) -> bool:
    for n in ast.walk(tree):
        if isinstance(n, BANNED_NODES):
            return False
        if isinstance(n, ast.Attribute):
            # Attributes can access dynamic behavior; do not execute.
            return False
        if isinstance(n, ast.Call):
            if not isinstance(n.func, ast.Name) or n.func.id not in PURE_BUILTINS:
                return False
        if isinstance(n, ast.Name):
            if n.id.startswith("__") or n.id in {"input", "exec", "eval", "open", "breakpoint", "globals", "locals"}:
                return False
    return True


def main() -> None:
    visited = run = skipped = 0
    failures = []
    for path in sorted((ROOT / "book/chapters").glob("[0-9][0-9]-*.md")):
        content = path.read_text(encoding="utf-8")
        for idx, (source, expected) in enumerate(BLOCK.findall(content), 1):
            visited += 1
            try:
                tree = ast.parse(source)
            except SyntaxError:
                skipped += 1
                continue
            if not is_pure(tree) or len(source) > 2600:
                skipped += 1
                continue
            with tempfile.TemporaryDirectory(prefix="syllanix-pure-") as temp:
                result = subprocess.run(
                    [sys.executable, "-I", "-S", "-B", "-c", source],
                    cwd=temp,
                    env={"PATH": os.environ.get("PATH", "")},
                    text=True,
                    capture_output=True,
                    timeout=2,
                    check=False,
                )
            if result.returncode or result.stdout.strip() != expected.strip():
                failures.append((path.name, idx, result.returncode,
                                 repr(result.stdout.strip()[:200]), repr(expected.strip()[:200]), result.stderr[-120:]))
            run += 1
    print(f"PURE EXAMPLES: scanned={visited}, executed={run}, skipped={skipped}, failures={len(failures)}")
    for info in failures[:25]:
        print("FAIL:", *info)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
