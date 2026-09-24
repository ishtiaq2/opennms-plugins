#!/usr/bin/env bash
# Uninstall ONE plugin from the running OpenNMS: delete its KAR from ./deploy (Karaf then
# uninstalls the KAR and its features) and wait until OpenNMS no longer lists its UI extensions.
#
#   scripts/undeploy-plugin.sh node-inventory                       # a demo plugin
#   scripts/undeploy-plugin.sh my-plugin.kar                        # any KAR in ./deploy (file name or path)
#
# Options:
#   --timeout SEC   how long to wait (default 120)
#   --no-wait       delete the file and return
set -euo pipefail
# shellcheck source=scripts/lib.sh
. "$(dirname "$0")/lib.sh"

TIMEOUT=120; WAIT=1; ARG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --timeout) TIMEOUT=${2:?--timeout needs a number}; shift 2 ;;
    --no-wait) WAIT=0; shift ;;
    -h|--help) lab_usage; exit 0 ;;
    -*) echo "unknown option $1" >&2; exit 2 ;;
    *) [ -z "$ARG" ] || { echo "one plugin at a time" >&2; exit 2; }; ARG=$1; shift ;;
  esac
done
[ -n "$ARG" ] || { lab_usage; exit 2; }

DEPLOY_DIR="$REPO/deploy"
KAR=""
for candidate in "$DEPLOY_DIR/$(basename "$ARG")" "$DEPLOY_DIR/$(basename "$ARG").kar" "$DEPLOY_DIR/opennms-lab-$ARG-plugin.kar"; do
  case "$candidate" in *.kar) ;; *) continue ;; esac
  if [ -f "$candidate" ]; then KAR=$candidate; break; fi
done
if [ -z "$KAR" ]; then
  echo "No KAR for '$ARG' in deploy/. Deployed now:" >&2
  for k in "$DEPLOY_DIR"/*.kar; do [ -f "$k" ] && echo "  $(basename "$k")" >&2; done
  exit 1
fi
NAME=$(basename "$KAR")

# Read the extension ids before the file is gone.
EXTENSIONS=$(python3 "$REPO/scripts/kar_info.py" --get extensions "$KAR" 2>/dev/null || true)
rm -f -- "$KAR"
echo "Removed deploy/$NAME: Karaf uninstalls KAR '${NAME%.kar}' and its features."
[ "$WAIT" = 1 ] || exit 0
[ -n "$EXTENSIONS" ] || { echo "(no UI extension in it to wait for)"; exit 0; }

set +e; lab_check_login; rc=$?; set -e
case "$rc" in
  0) ;;
  2) echo "OpenNMS is not running; the plugin will simply not be installed at the next start."; exit 0 ;;
  3) exit 1 ;;
  *) echo "Waiting anyway..." ;;
esac

start=$SECONDS
while :; do
  registered=$(lab_extensions)
  left=""
  while read -r id _; do
    if [ -n "$id" ] && lab_has_extension "$id" <<<"$registered"; then left+="$id "; fi
  done <<<"$EXTENSIONS"
  [ -z "$left" ] && break
  if [ $((SECONDS - start)) -ge "$TIMEOUT" ]; then
    echo "Timed out: OpenNMS still lists $left(see docs/09-troubleshooting.md)." >&2
    exit 1
  fi
  sleep 2
done
echo "Gone after $((SECONDS - start))s: $(awk '{print $1}' <<<"$EXTENSIONS" | paste -sd' ' -) no longer listed. Reload the browser tab to update the Plugins menu."
