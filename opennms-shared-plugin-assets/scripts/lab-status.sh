#!/usr/bin/env bash
# One screen with the state of the whole lab: containers, OpenNMS health and version, the shared
# assets folder, the KARs in ./deploy and the UI extensions OpenNMS has registered.
#
#   scripts/lab-status.sh
set -uo pipefail
# shellcheck source=scripts/lib.sh
. "$(dirname "$0")/lib.sh"

ENGINE=$(lab_engine 2>/dev/null || true)

echo "== Containers"
if [ -n "$ENGINE" ]; then
  rows=$("$ENGINE" ps -a --format '{{.Names}}\t{{.Status}}\t{{.Image}}' 2>/dev/null \
    | awk -F'\t' -v a="$HORIZON_CONTAINER" -v b="$DB_CONTAINER" '$1 == a || $1 == b { printf "  %-28s %-32s %s\n", $1, $2, $3 }')
  echo "${rows:-  no lab containers (podman-compose up -d)}"
else
  echo "  (neither podman nor docker found)"
fi

echo
echo "== OpenNMS at $ONMS_URL/opennms/"
probe=$(curl -s --max-time 10 "$ONMS_URL/opennms/rest/health/probe" 2>/dev/null)
echo "  health probe: ${probe:-no answer}"
LOGIN=1
if info=$(lab_get /rest/info -f -H 'Accept: application/json' 2>/dev/null); then
  version=$(python3 -c 'import json, sys; d = json.load(sys.stdin); print(d.get("displayVersion") or d.get("version"))' <<<"$info" 2>/dev/null)
  echo "  version: ${version:-?} (login '$ONMS_USER' accepted)"
else
  LOGIN=0
  lab_check_login 2>&1 | sed 's/^/  /'
fi

echo
echo "== Shared assets: ./shared-assets -> $ONMS_URL/opennms/assets/shared/"
python3 - "$REPO/shared-assets/manifest.json" <<'PY'
import json, sys
try:
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    print(f"  on disk: manifest revision {m.get('revision')}; icons: {len(m.get('icons') or {})}, "
          f"images: {len(m.get('images') or {})}, node icon rules: {len(m.get('nodeIconRules') or [])}")
except (OSError, ValueError) as e:
    print(f"  on disk: manifest.json unreadable ({e})")
PY
served=$(curl -s --max-time 10 -f "$ONMS_URL/opennms/assets/shared/manifest.json" 2>/dev/null \
  | python3 -c 'import json, sys; print(json.load(sys.stdin).get("revision"))' 2>/dev/null)
if [ -n "$served" ]; then echo "  served:  manifest revision $served (no login needed)"
else echo "  served:  manifest.json not reachable (scripts/verify-assets.sh explains)"; fi

echo
echo "== Plugin KARs in ./deploy (watched by Karaf as /opt/opennms-lab-deploy)"
REGISTERED=""
[ "$LOGIN" = 1 ] && REGISTERED=$(lab_extensions)
shopt -s nullglob
kars=("$REPO"/deploy/*.kar)
if [ ${#kars[@]} -eq 0 ]; then
  echo "  none (scripts/deploy-plugin.sh <plugin>)"
fi
for kar in "${kars[@]}"; do
  ids=$(python3 "$REPO/scripts/kar_info.py" --get extensions "$kar" 2>/dev/null | awk '{print $1}')
  line="  $(basename "$kar")"
  if [ -z "$ids" ]; then line+="  (no UI extension)"; fi
  for id in $ids; do
    if [ "$LOGIN" = 0 ]; then line+="  $id: ?"
    elif lab_has_extension "$id" <<<"$REGISTERED"; then line+="  $id: registered"
    else line+="  $id: NOT registered"; fi
  done
  echo "$line"
done

echo
echo "== UI extensions registered in OpenNMS (GET /opennms/rest/plugins)"
if [ "$LOGIN" = 0 ]; then
  echo "  (needs the login)"
elif [ -z "$REGISTERED" ]; then
  echo "  none"
else
  while read -r id root module; do
    echo "  $id  ->  /opennms/ui/#/plugins/$id/$root/$module"
  done <<<"$REGISTERED"
fi
