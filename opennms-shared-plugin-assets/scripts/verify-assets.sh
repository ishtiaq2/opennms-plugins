#!/usr/bin/env bash
# Receiver-side check: does OpenNMS really serve the shared folder the way the plugins expect?
#
#   scripts/verify-assets.sh               # anonymous HTTP checks of every manifest entry
#   scripts/verify-assets.sh --live-drop   # + write a file into ./shared-assets and fetch it at once
#   scripts/verify-assets.sh --plugins     # + check the UI-extension REST endpoints (needs a login)
#
# Settings come from .env or the environment (scripts/lib.sh): ONMS_URL, ONMS_USER, ONMS_PASS, and
# SHARED_DIR (default: the repo's shared-assets folder, i.e. the bind-mount source).
set -uo pipefail
# shellcheck source=scripts/lib.sh
. "$(dirname "$0")/lib.sh"
SHARED_DIR=${SHARED_DIR:-$REPO/shared-assets}
BASE="$ONMS_URL/opennms/assets/shared"
LIVE_DROP=0; PLUGINS=0
for a in "$@"; do
  case "$a" in
    --live-drop) LIVE_DROP=1 ;;
    --plugins) PLUGINS=1 ;;
    -h|--help) lab_usage; exit 0 ;;
    *) echo "unknown option $a" >&2; exit 2 ;;
  esac
done

PASS=0; FAIL=0; WARN=0
pass() { printf 'PASS  %s\n' "$*"; PASS=$((PASS+1)); }
fail() { printf 'FAIL  %s\n' "$*"; FAIL=$((FAIL+1)); }
warn() { printf 'WARN  %s\n' "$*"; WARN=$((WARN+1)); }

# headers of a GET (body discarded); curl -D - prints them, tr strips CR
headers() { curl -sS -o /dev/null -D - "$@" | tr -d '\r'; }
status_of() { awk 'NR==1{print $2}' <<<"$1"; }
header_of() { grep -i "^$2:" <<<"$1" | head -1 | cut -d' ' -f2-; }

echo "== Shared folder served by Jetty at $BASE/"
H=$(headers "$BASE/manifest.json")
if [ "$(status_of "$H")" = 200 ]; then
  pass "manifest.json -> 200 without login ($(header_of "$H" Content-Type))"
else
  fail "manifest.json -> $(status_of "$H" || echo 'no answer'). Is OpenNMS up and ./shared-assets mounted at jetty-webapps/opennms/assets/shared?"
  echo; echo "$PASS passed, $FAIL failed"; exit 1
fi

PATHS=$(curl -sS "$BASE/manifest.json" | python3 -c '
import json, sys
m = json.load(sys.stdin)
for section in ("icons", "images"):
    for key, e in (m.get(section) or {}).items():
        print(e["path"])')

for p in $PATHS; do
  H=$(headers "$BASE/$p")
  s=$(status_of "$H"); ct=$(header_of "$H" Content-Type); cc=$(header_of "$H" Cache-Control)
  if [ "$s" != 200 ]; then fail "$p -> HTTP $s"; continue; fi
  case "$p" in
    *.svg) want=image/svg+xml ;; *.png) want=image/png ;; *.webp) want=image/webp ;;
    *.jpg|*.jpeg) want=image/jpeg ;; *.gif) want=image/gif ;; *) want="" ;;
  esac
  if [ -n "$want" ] && [ "${ct%%;*}" != "$want" ]; then fail "$p -> Content-Type '$ct' (expected $want)"; continue; fi
  if [[ "$cc" == *max-age=3600* ]]; then pass "$p -> 200 $ct, Cache-Control: $cc"
  else warn "$p -> 200 $ct, but Cache-Control is '$cc' (expected max-age=3600,public under /opennms/assets/)"; fi
done

H=$(headers "$BASE/icons/")
s=$(status_of "$H")
if [ "$s" = 403 ] || [ "$s" = 404 ]; then pass "directory listing disabled (icons/ -> $s): plugins must use manifest.json to discover files"
else warn "icons/ -> $s: directory listing seems enabled"; fi

H=$(headers "$ONMS_URL/opennms/favicon.ico")
cc=$(header_of "$H" Cache-Control)
if [[ "$cc" == *no-store* ]]; then pass "contrast: /opennms/favicon.ico (outside /assets/) -> Cache-Control: $cc (jetty.xml RewriteHandler rule)"
else warn "contrast: /opennms/favicon.ico -> Cache-Control '$cc' (expected no-store; custom jetty.xml?)"; fi

if [ "$LIVE_DROP" = 1 ]; then
  echo; echo "== Live drop into $SHARED_DIR"
  name="icons/.verify-$$.svg"; final="icons/verify-$$.svg"
  printf '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8"><rect width="8" height="8"/></svg>\n' > "$SHARED_DIR/$name"
  chmod 644 "$SHARED_DIR/$name"; mv "$SHARED_DIR/$name" "$SHARED_DIR/$final"
  H=$(headers "$BASE/$final")
  if [ "$(status_of "$H")" = 200 ]; then pass "a file written on the host is served immediately ($final)"
  else fail "$final -> $(status_of "$H") right after writing it on the host (mounted the right folder? permissions?)"; fi
  rm -f "$SHARED_DIR/$final"
  H=$(headers "$BASE/$final")
  if [ "$(status_of "$H")" = 404 ]; then pass "and it is gone (404) as soon as it is deleted"
  else fail "$final still served after delete"; fi
fi

if [ "$PLUGINS" = 1 ]; then
  echo; echo "== UI-extension endpoints (authenticated as $ONMS_USER)"
  lab_check_login || fail "cannot log in as $ONMS_USER (see the line above); the checks below will fail too"
  LIST=$(curl -sS -u "$ONMS_USER:$ONMS_PASS" -H 'Accept: application/json' "$ONMS_URL/opennms/rest/plugins")
  ROWS=$(python3 -c '
import json, sys
try:
    data = json.loads(sys.argv[1])
except ValueError:
    sys.exit(1)
for p in data:
    print(p["extensionId"], p["resourceRootPath"], p["moduleFileName"])' "$LIST") || { fail "/opennms/rest/plugins did not return JSON: ${LIST:0:120}"; ROWS=""; }
  [ -n "$ROWS" ] && pass "/opennms/rest/plugins lists: $(awk '{print $1}' <<<"$ROWS" | paste -sd, -)"
  while read -r id root file; do
    [ -z "${id:-}" ] && continue
    H=$(headers -u "$ONMS_USER:$ONMS_PASS" "$ONMS_URL/opennms/rest/plugins/ui-extension/module/$id?path=$root/$file")
    if [ "$(status_of "$H")" = 200 ]; then pass "$id module -> 200 $(header_of "$H" Content-Type)"
    else fail "$id module -> $(status_of "$H")"; fi
    H=$(headers -u "$ONMS_USER:$ONMS_PASS" "$ONMS_URL/opennms/rest/plugins/ui-extension/css/$id")
    case "$(status_of "$H")" in
      200) pass "$id style.css -> 200 $(header_of "$H" Content-Type)" ;;
      204) warn "$id style.css -> 204 (no $root/style.css in the bundle)" ;;
      *) fail "$id style.css -> $(status_of "$H")" ;;
    esac
  done <<<"$ROWS"
  for id in labNodeInventory labIconCatalog; do
    lab_has_extension "$id" <<<"$ROWS" || warn "$id not deployed yet (scripts/build-plugins.sh, then scripts/deploy-plugin.sh <name>)"
  done
fi

echo; echo "$PASS passed, $WARN warnings, $FAIL failed"
[ "$FAIL" = 0 ]
