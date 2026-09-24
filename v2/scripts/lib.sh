# shellcheck shell=bash
# Shared settings for the scripts in this folder:   . "$(dirname "$0")/lib.sh"
#
# Reads the repository's .env like compose does (KEY=VALUE lines, no shell expansion), without
# overriding variables already set in the environment, and sets these defaults:
#   ONMS_URL            http://localhost:<ONMS_HTTP_PORT> (or the ONMS_HTTP_BIND address, if specific)
#   ONMS_USER/ONMS_PASS admin / admin
#   CONTAINER_ENGINE    podman if installed, else docker (see lab_engine)
#   HORIZON_CONTAINER   onms-shared-assets-horizon   (container_name in compose.yml)
#   DB_CONTAINER        onms-shared-assets-db
# Requires bash, curl and python3.

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export REPO

lab_load_env() {
  local file=$REPO/.env line key val
  [ -f "$file" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    line=${line%$'\r'}
    [[ "$line" =~ ^[[:space:]]*(#|$) ]] && continue
    [[ "$line" =~ ^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=(.*)$ ]] || continue
    key=${BASH_REMATCH[2]}
    val=${BASH_REMATCH[3]}
    val=${val#"${val%%[![:space:]]*}"}                       # leading blanks
    if [[ "$val" =~ ^\"(.*)\"[[:space:]]*$ || "$val" =~ ^\'(.*)\'[[:space:]]*$ ]]; then
      val=${BASH_REMATCH[1]}                                 # one pair of quotes
    else
      val=${val%"${val##*[![:space:]]}"}                     # trailing blanks
    fi
    [ -n "${!key+x}" ] && continue                           # the environment wins, as in compose
    printf -v "$key" '%s' "$val"
    export "${key?}"
  done < "$file"
}

lab_load_env

: "${ONMS_HTTP_PORT:=8980}"
if [ -z "${ONMS_URL:-}" ]; then
  case "${ONMS_HTTP_BIND:-127.0.0.1}" in
    ''|0.0.0.0|127.0.0.1|localhost|::|'[::]') ONMS_URL="http://localhost:$ONMS_HTTP_PORT" ;;
    \[*) ONMS_URL="http://$ONMS_HTTP_BIND:$ONMS_HTTP_PORT" ;;
    *:*) ONMS_URL="http://[$ONMS_HTTP_BIND]:$ONMS_HTTP_PORT" ;;
    *) ONMS_URL="http://$ONMS_HTTP_BIND:$ONMS_HTTP_PORT" ;;
  esac
fi
ONMS_URL=${ONMS_URL%/}
: "${ONMS_USER:=admin}" "${ONMS_PASS:=admin}"
: "${HORIZON_CONTAINER:=onms-shared-assets-horizon}" "${DB_CONTAINER:=onms-shared-assets-db}"
export ONMS_URL ONMS_USER ONMS_PASS HORIZON_CONTAINER DB_CONTAINER

# lab_usage: print the calling script's header comment (its help text)
lab_usage() {
  awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"
}

# The container engine to use for "exec", "logs" and "ps"; prints nothing and fails if none.
lab_engine() {
  if [ -n "${CONTAINER_ENGINE:-}" ]; then printf '%s\n' "$CONTAINER_ENGINE"
  elif command -v podman >/dev/null 2>&1; then echo podman
  elif command -v docker >/dev/null 2>&1; then echo docker
  else return 1
  fi
}

# lab_http_status URL [curl options...] -> the HTTP status code, 000 when nothing answers
lab_http_status() {
  local url=$1; shift
  curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$@" "$url" 2>/dev/null || true
}

# lab_get PATH [curl options...] -> body of an authenticated GET below $ONMS_URL/opennms
lab_get() {
  local path=$1; shift
  curl -s --max-time 15 -u "$ONMS_USER:$ONMS_PASS" "$@" "$ONMS_URL/opennms$path"
}

# lab_check_login: 0 when OpenNMS accepts ONMS_USER/ONMS_PASS. Otherwise prints why and returns
# 2 (nothing answers), 3 (login refused) or 4 (anything else, usually "still starting").
lab_check_login() {
  local code
  code=$(lab_http_status "$ONMS_URL/opennms/rest/info" -u "$ONMS_USER:$ONMS_PASS")
  case "$code" in
    200) return 0 ;;
    000) echo "No answer from $ONMS_URL. Is OpenNMS running? Try scripts/wait-for-opennms.sh" >&2; return 2 ;;
    401|403) echo "OpenNMS refused the login '$ONMS_USER' (HTTP $code). If you changed the admin password, put it in .env as ONMS_PASS=..." >&2; return 3 ;;
    *) echo "HTTP $code from $ONMS_URL/opennms/rest/info; OpenNMS is probably still starting (scripts/wait-for-opennms.sh)" >&2; return 4 ;;
  esac
}

# lab_extensions -> "extensionId resourceRootPath moduleFileName" for every UI extension OpenNMS
# lists at /opennms/rest/plugins (nothing on error)
lab_extensions() {
  { lab_get /rest/plugins -H 'Accept: application/json' || true; } | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
for p in data if isinstance(data, list) else []:
    print(p.get("extensionId"), p.get("resourceRootPath"), p.get("moduleFileName"))'
}

# lab_sha256 < data -> hex digest (portable: no sha256sum/shasum differences)
lab_sha256() {
  python3 -c 'import hashlib, sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())'
}

# lab_module_sha256 ID ROOT MODULE -> digest of the module as OpenNMS serves it right now
lab_module_sha256() {
  { lab_get "/rest/plugins/ui-extension/module/$1?path=$2/$3" -f || true; } | lab_sha256
}

# lab_has_extension ID < "lab_extensions output" -> 0 when ID is listed
lab_has_extension() {
  awk -v id="$1" '$1 == id { found = 1 } END { exit !found }'
}
