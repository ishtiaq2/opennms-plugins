#!/usr/bin/env python3
"""Checks the relative links of every Markdown file in the repository.

    scripts/check_links.py            # from the repository root; exit 1 on a broken link

A link must point at an existing file or folder, and a '#fragment' on a Markdown file must match one
of its headings, turned into an anchor the way GitHub does it. Links with a scheme (https:, mailto:)
and text inside code are ignored.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"node_modules", "target", "dist", ".git"}


def slug(heading: str) -> str:
    h = heading.strip().lower().replace("`", "")
    h = re.sub(r"[^\w\- ]", "", h)
    return h.replace(" ", "-")


def without_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def anchors(md: Path) -> set[str]:
    text = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8"), flags=re.S)
    found: set[str] = set()
    seen: dict[str, int] = {}
    for m in re.finditer(r"^#{1,6}\s+(.*)$", text, re.M):
        s = slug(m.group(1))
        if s in seen:
            seen[s] += 1
            found.add(f"{s}-{seen[s]}")
        else:
            seen[s] = 0
            found.add(s)
    return found


def main() -> int:
    bad = links = 0
    for md in sorted(ROOT.rglob("*.md")):
        if SKIP & set(md.relative_to(ROOT).parts):
            continue
        for m in re.finditer(r"\]\(([^)\s]+)\)", without_code(md.read_text(encoding="utf-8"))):
            target = m.group(1)
            if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue
            links += 1
            path, _, fragment = target.partition("#")
            dest = (md.parent / path).resolve() if path else md
            where = md.relative_to(ROOT)
            if not dest.exists():
                print(f"{where}: no such file: {target}")
                bad += 1
            elif fragment and dest.suffix == ".md" and fragment not in anchors(dest):
                print(f"{where}: no such heading: {target}")
                bad += 1
    print(f"{links} relative links checked, {bad} broken")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
