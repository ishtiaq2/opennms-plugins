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

step "compose mounts point at folders of this repository"
run python3 - <<'PY2'
import re, sys, pathlib
text = pathlib.Path('compose.yml').read_text()
bad = [src for src in re.findall(r'^\s*-\s*(\./[^:]+):', text, re.M) if not pathlib.Path(src).is_dir()]
for b in bad:
    print(f'{b} is mounted by compose.yml but is not a folder here')
sys.exit(1 if bad else 0)
PY2

step "etc-overlay: the extra Karaf deploy watcher"
run python3 - <<'PY2'
import re, sys, pathlib
cfg = pathlib.Path('etc-overlay/org.apache.felix.fileinstall-lab.cfg').read_text()
props = dict(l.split('=', 1) for l in cfg.splitlines() if '=' in l and not l.lstrip().startswith('#'))
props = {k.strip(): v.strip() for k, v in props.items()}
flt = re.compile(props['felix.fileinstall.filter'])   # FileInstall's Scanner uses matcher(name).matches()
ok = all([props['felix.fileinstall.dir'] == '/opt/opennms-lab-deploy',
          flt.fullmatch('opennms-lab-node-inventory-plugin.kar'),
          not flt.fullmatch('.opennms-lab-node-inventory-plugin.kar.part'),
          not flt.fullmatch('README.md'),
          '\\' not in props['felix.fileinstall.filter']])
print('filter and dir as expected' if ok else f'unexpected values: {props}')
sys.exit(0 if ok else 1)
PY2

step "Python scripts compile"
run python3 -m py_compile scripts/assets.py scripts/check_plugins.py scripts/kar_info.py tests/scripts/test_tools.py

step "tooling unit tests (kar_info, check_plugins on KARs, lib.sh)"
run python3 -m unittest discover -s tests/scripts

step "shell scripts"
if have shellcheck; then run shellcheck -x scripts/*.sh; else echo "skipped (shellcheck not installed)"; for f in scripts/*.sh; do run bash -n "$f"; done; fi
run bash -c 'bad=0; for f in scripts/*.sh scripts/*.py; do [ "$f" = scripts/lib.sh ] && continue; [ -x "$f" ] || { echo "$f is not executable"; bad=1; }; done; exit $bad'

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
