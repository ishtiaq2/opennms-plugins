#!/usr/bin/env bash
# Build the demo plugins end to end:
#   shared helper (tsc) -> Vue module (vite, written into plugin/src/main/resources/<root>/)
#   -> contract check -> bundle + features + KAR (maven)
#
#   scripts/build-plugins.sh                        # both plugins
#   scripts/build-plugins.sh node-inventory         # one plugin (names = folders in plugins/)
#   scripts/build-plugins.sh --no-maven [names]     # JS only (the built modules are committed, so Maven can run later)
#
# The KARs end up in plugins/<name>/assembly/kar/target/opennms-lab-<name>-plugin.kar.
# Nothing is deployed: install them one at a time with scripts/deploy-plugin.sh <name>.
# OIA_VERSION=x.y.z overrides <opennms.api.version> when you target another OpenNMS release.
set -euo pipefail
cd "$(dirname "$0")/.."

MAVEN=1; NAMES=()
for a in "$@"; do
  case "$a" in
    --no-maven) MAVEN=0 ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    -*) echo "unknown option $a" >&2; exit 2 ;;
    *) if [ ! -d "plugins/$a/ui" ]; then
         echo "no plugin 'plugins/$a' (have: $(for d in plugins/*/ui; do basename "$(dirname "$d")"; done | paste -sd' ' -))" >&2
         exit 2
       fi
       NAMES+=("$a") ;;
  esac
done
if [ ${#NAMES[@]} -eq 0 ]; then
  for d in plugins/*/ui; do NAMES+=("$(basename "$(dirname "$d")")"); done
fi

echo "== npm workspaces"
if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi
npm test
npm run build:helper
for n in "${NAMES[@]}"; do
  echo "== Vue module: $n"
  npm run build -w "plugins/$n/ui"
done

echo "== contract check"
BUNDLES=()
for n in "${NAMES[@]}"; do BUNDLES+=("plugins/$n/plugin"); done
python3 scripts/check_plugins.py "${BUNDLES[@]}"

[ "$MAVEN" = 1 ] || exit 0
for n in "${NAMES[@]}"; do
  echo "== maven: $n (OIA ${OIA_VERSION:-1.6.1 from the POM})"
  mvn -B -f "plugins/$n/pom.xml" ${OIA_VERSION:+-Dopennms.api.version=$OIA_VERSION} clean package
done

echo
echo "Built:"
for n in "${NAMES[@]}"; do
  kar="plugins/$n/assembly/kar/target/opennms-lab-$n-plugin.kar"
  echo "  $kar  ($(wc -c < "$kar" | tr -d ' ') bytes)"
  python3 scripts/check_plugins.py "$kar" >/dev/null || echo "  ^ check_plugins.py reports a FAIL for this KAR; run it to see why"
done
echo
echo "Next, one plugin at a time:"
for n in "${NAMES[@]}"; do echo "  scripts/deploy-plugin.sh $n"; done
