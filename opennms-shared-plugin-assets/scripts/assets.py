#!/usr/bin/env python3
"""Manage the shared-assets folder that OpenNMS serves at /opennms/assets/shared/.

    python3 scripts/assets.py list
    python3 scripts/assets.py validate
    python3 scripts/assets.py add ~/Downloads/lb.svg --key load-balancer --label "Load balancer" --category LoadBalancers
    python3 scripts/assets.py add ~/Pictures/rack.png --as photos/rack-a.png --kind image --key rack-a
    python3 scripts/assets.py bump

Why a script instead of "just copy the file"?  Copying is enough for Jetty: the next request
serves the new file. The script adds the three things copying alone does not do:
  * atomic writes (temp file + rename), so Jetty never serves a half-written file and never
    has an existing file truncated under its memory-mapped cache;
  * world-readable permissions, because the container reads the folder as uid 10001;
  * a manifest.json update + revision bump, which is how plugins learn about new icons
    (Jetty's directory listing is disabled) and how browsers are told to drop the copy
    they cached for an hour.
Only the Python 3 standard library is used.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent / "shared-assets"
URL_BASE = "/opennms/assets/shared/"
SAFE_PATH = re.compile(r"^(?!/)(?!.*(^|/)\.\.?(/|$))[A-Za-z0-9._/-]+$")
KNOWN_TYPES = {".svg", ".svgz", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico", ".json", ".css", ".woff", ".woff2"}


def load_manifest(root: Path) -> dict:
    with open(root / "manifest.json", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: Path) -> None:
    """mkdir -p, but every directory we create is 0755 whatever the umask (uid 10001 must traverse it)."""
    missing = []
    while not path.exists():
        missing.append(path)
        path = path.parent
    for d in reversed(missing):
        d.mkdir()
        os.chmod(d, 0o755)


def atomic_write_bytes(dest: Path, data: bytes) -> None:
    ensure_dir(dest.parent)
    fd, tmp = tempfile.mkstemp(prefix=f".{dest.name}.", suffix=".tmp", dir=dest.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, dest)  # atomic on the same filesystem
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def save_manifest(root: Path, manifest: dict) -> None:
    atomic_write_bytes(root / "manifest.json", (json.dumps(manifest, indent=2, ensure_ascii=True) + "\n").encode())


def bump_revision(manifest: dict) -> None:
    rev = manifest.get("revision", 0)
    manifest["revision"] = rev + 1 if isinstance(rev, int) else f"{rev}.1"


def cmd_list(args: argparse.Namespace) -> int:
    m = load_manifest(args.root)
    print(f"revision {m.get('revision')}  (URLs get ?rev={m.get('revision')})\n")
    for section in ("icons", "images"):
        for key, entry in (m.get(section) or {}).items():
            path = entry.get("path", "")
            exists = "ok " if (args.root / path).is_file() else "MISSING"
            print(f"{exists:7} {section[:-1]:5} {key:16} {URL_BASE}{path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root: Path = args.root
    problems: list[str] = []
    warnings: list[str] = []
    try:
        m = load_manifest(root)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL  manifest.json unreadable: {e}")
        return 1
    if m.get("schemaVersion") != 1:
        problems.append("schemaVersion must be 1")
    if not isinstance(m.get("revision"), (int, str)):
        problems.append("revision must be an integer or string")
    referenced: set[str] = {"manifest.json", "manifest.schema.json", "README.md"}
    for section in ("icons", "images"):
        for key, entry in (m.get(section) or {}).items():
            path = entry.get("path") if isinstance(entry, dict) else None
            if not isinstance(path, str) or not SAFE_PATH.match(path):
                problems.append(f"{section}.{key}: bad path {path!r} (relative, no '.' or '..' segments)")
                continue
            referenced.add(path)
            p = root / path
            if not p.is_file():
                problems.append(f"{section}.{key}: {path} does not exist")
            elif p.suffix.lower() not in KNOWN_TYPES:
                warnings.append(f"{section}.{key}: {p.suffix} may be served without a useful Content-Type")
    icons = m.get("icons") or {}
    for i, rule in enumerate(m.get("nodeIconRules") or [], 1):
        if rule.get("icon") not in icons:
            problems.append(f"nodeIconRules[{i}] points at unknown icon {rule.get('icon')!r}")
        match = rule.get("match") or {}
        if not match:
            problems.append(f"nodeIconRules[{i}] has no conditions (it would never match)")
        pattern = match.get("labelPattern")
        if pattern is not None:
            try:
                re.compile(pattern)
            except re.error as e:
                warnings.append(f"nodeIconRules[{i}].labelPattern does not compile in Python ({e}); check it is valid JavaScript")
    if m.get("defaultIcon") not in icons:
        problems.append(f"defaultIcon {m.get('defaultIcon')!r} is not an icon key")

    # The container reads the bind mount as uid 10001 (not the owner), so "other" needs r / x.
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        for name in dirnames:
            full = d / name
            if full.is_symlink():
                warnings.append(f"{full.relative_to(root)} is a symlink: it resolves INSIDE the container; copy the files instead")
            elif not (full.stat().st_mode & stat.S_IXOTH and full.stat().st_mode & stat.S_IROTH):
                problems.append(f"directory {full.relative_to(root)} is not o+rx (chmod 755)")
        for name in filenames:
            full = d / name
            rel = str(full.relative_to(root))
            if full.is_symlink():
                warnings.append(f"{rel} is a symlink: it resolves INSIDE the container; copy the file instead")
                continue
            if name.startswith(".") and name.endswith(".tmp"):
                warnings.append(f"{rel} looks like a leftover temp file")
            if not full.stat().st_mode & stat.S_IROTH:
                problems.append(f"{rel} is not world-readable (chmod 644)")
            if rel not in referenced and not name.startswith("."):
                warnings.append(f"{rel} is not in manifest.json (reachable by URL, invisible to catalog lookups)")
    for w in warnings:
        print(f"WARN  {w}")
    for p in problems:
        print(f"FAIL  {p}")
    print(f"\n{len(problems)} problem(s), {len(warnings)} warning(s)")
    return 1 if problems else 0


def cmd_add(args: argparse.Namespace) -> int:
    root: Path = args.root
    src = Path(args.source).expanduser()
    if not src.is_file():
        print(f"no such file: {src}", file=sys.stderr)
        return 2
    kind = args.kind
    section = "icons" if kind == "icon" else "images"
    rel = args.as_path or (f"icons/{src.name}" if kind == "icon" else f"images/{src.name}")
    if not SAFE_PATH.match(rel):
        print(f"refusing path {rel!r}: use letters, digits, . _ - / and no '..'", file=sys.stderr)
        return 2
    key = args.key or Path(rel).stem
    dest = root / rel
    replacing = dest.exists()
    atomic_write_bytes(dest, src.read_bytes())

    m = load_manifest(root)
    m.setdefault(section, {})
    entry = {"path": rel}
    if args.label:
        entry["label"] = args.label
    elif key in m[section] and "label" in m[section][key]:
        entry["label"] = m[section][key]["label"]
    m[section][key] = entry
    if args.category:
        if kind != "icon":
            print("--category only makes sense for icons", file=sys.stderr)
            return 2
        # Appended at the end: rules are evaluated top to bottom and the first match wins,
        # so edit manifest.json by hand if the new rule must win over an existing one.
        m.setdefault("nodeIconRules", []).append({"icon": key, "match": {"categories": list(args.category)}})
    bump_revision(m)
    save_manifest(root, m)
    what = "replaced" if replacing else "added"
    print(f"{what} {rel} as {section[:-1]} '{key}', manifest revision -> {m['revision']}")
    print(f"served at {URL_BASE}{rel}  (no restart needed)")
    return 0


def cmd_bump(args: argparse.Namespace) -> int:
    m = load_manifest(args.root)
    bump_revision(m)
    save_manifest(args.root, m)
    print(f"manifest revision -> {m['revision']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="shared-assets folder (default: %(default)s)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="print the catalog and the URL of every entry")
    sub.add_parser("validate", help="check manifest, files and permissions")
    add = sub.add_parser("add", help="copy a file in atomically and register it in manifest.json")
    add.add_argument("source")
    add.add_argument("--as", dest="as_path", help="destination path inside the folder (default icons/<name> or images/<name>)")
    add.add_argument("--key", help="catalog key (default: file name without extension)")
    add.add_argument("--label", help="human-readable label")
    add.add_argument("--kind", choices=("icon", "image"), default="icon")
    add.add_argument("--category", action="append", help="add a node-icon rule for this surveillance category (repeatable)")
    sub.add_parser("bump", help="increase the manifest revision (after editing files by hand)")
    args = ap.parse_args()
    return {"list": cmd_list, "validate": cmd_validate, "add": cmd_add, "bump": cmd_bump}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
