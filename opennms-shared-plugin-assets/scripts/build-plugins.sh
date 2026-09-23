#!/usr/bin/env bash
# Build both demo plugins end to end:
#   shared helper (tsc) -> Vue modules (vite, written into plugin/src/main/resources/<root>/)
#   -> contract check -> bundles + features + KARs (maven) -> overlay/deploy/*.kar
#
#   scripts/build-plugins.sh            # everything
#   scripts/build-plugins.sh --no-maven # JS only (the built modules are committed, so Maven can run later)
set -euo pipefail
cd "$(dirname "$0")/.."
MAVEN=1
[ "${1:-}" = "--no-maven" ] && MAVEN=0

echo "== npm workspaces"
if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi
npm test
npm run build:ui
echo "== contract check"
python3 scripts/check_plugins.py

if [ "$MAVEN" = 1 ]; then
  # OIA_VERSION=x.y.z overrides <opennms.api.version> when you target another OpenNMS release
  echo "== maven (OIA ${OIA_VERSION:-1.6.1 from the POMs})"
  mvn -B -f plugins/pom.xml ${OIA_VERSION:+-Dopennms.api.version=$OIA_VERSION} clean package
  mkdir -p overlay/deploy
  cp -v plugins/*/assembly/kar/target/opennms-lab-*-plugin.kar overlay/deploy/
  cat <<MSG

KARs are in overlay/deploy/. The entrypoint copies them into \$OPENNMS_HOME/deploy/ at start:
  podman-compose restart horizon
or copy them into the running container without a restart:
  podman cp overlay/deploy/opennms-lab-node-inventory-plugin.kar onms-shared-assets-horizon:/usr/share/opennms/deploy/
  podman cp overlay/deploy/opennms-lab-icon-catalog-plugin.kar  onms-shared-assets-horizon:/usr/share/opennms/deploy/
MSG
fi
