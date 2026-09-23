#!/usr/bin/env bash
# Offline validation sweep for this repository (no OpenNMS needed). Optional tools are skipped
# when they are not installed.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
FAIL=0
step() { printf '\n== %s\n' "$*"; }
run() { if "$@"; then echo "ok"; else echo "FAILED: $*"; FAIL=1; fi; }
have() { command -v "$1" >/dev/null 2>&1; }

step "JSON files parse"
run python3 - <<'PY'
import json, pathlib, sys
bad = 0
for p in pathlib.Path('.').rglob('*.json'):
    if 'node_modules' in p.parts or 'dist' in p.parts:
        continue
    try:
        json.loads(p.read_text(encoding='utf-8'))
    except ValueError as e:
        print(f'{p}: {e}'); bad += 1
sys.exit(1 if bad else 0)
PY

step "XML files are well-formed"
run python3 - <<'PY'
import pathlib, sys, xml.dom.minidom
bad = 0
for p in pathlib.Path('.').rglob('*.xml'):
    if 'node_modules' in p.parts or 'target' in p.parts:
        continue
    try:
        xml.dom.minidom.parse(str(p))
    except Exception as e:
        print(f'{p}: {e}'); bad += 1
sys.exit(1 if bad else 0)
PY

step "compose.yml parses"
if have docker && docker compose version >/dev/null 2>&1; then run docker compose -f compose.yml config -q
elif have podman-compose; then run podman-compose -f compose.yml config >/dev/null
else run python3 -c "import yaml; yaml.safe_load(open('compose.yml'))" 2>/dev/null || echo "skipped (no compose tool, no PyYAML)"; fi

step "Python scripts compile"
run python3 -m py_compile scripts/assets.py scripts/check_plugins.py

step "shell scripts"
if have shellcheck; then run shellcheck scripts/*.sh; else echo "skipped (shellcheck not installed)"; for f in scripts/*.sh; do run bash -n "$f"; done; fi

step "shared-assets folder (manifest, files, permissions)"
run python3 scripts/assets.py validate

step "plugin contract (built modules vs. the 33.1.8 loader rules)"
run python3 scripts/check_plugins.py

if [ -d node_modules ]; then
  step "helper unit tests and type checks"
  run npm test --silent
  run npm run typecheck --silent
else
  step "npm checks skipped (run 'npm ci' first)"
fi

if have markdownlint-cli2; then step "markdown lint"; run markdownlint-cli2 "**/*.md"; fi

echo
if [ "$FAIL" = 0 ]; then echo "ALL CHECKS PASSED"; else echo "SOME CHECKS FAILED"; fi
exit "$FAIL"
