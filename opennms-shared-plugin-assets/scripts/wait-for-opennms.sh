#!/usr/bin/env bash
# Wait until OpenNMS is ready, and show what it is doing meanwhile.
#
#   scripts/wait-for-opennms.sh                  # wait up to 15 minutes
#   scripts/wait-for-opennms.sh --timeout 300
#
# "Ready" means GET /opennms/rest/health/probe answers "Everything is awesome", the same test as
# the container's health check. While waiting it prints, every 15 seconds, the stage OpenNMS is in:
# no answer yet (database setup, config tests), the web app starting, or the health checks that are
# not green yet (needs the login from .env). Exit 0 when ready; 1 on timeout, or when the Horizon
# container keeps stopping (its last log lines are printed).
set -uo pipefail
# shellcheck source=scripts/lib.sh
. "$(dirname "$0")/lib.sh"

TIMEOUT=900
while [ $# -gt 0 ]; do
  case "$1" in
    --timeout) TIMEOUT=${2:?--timeout needs a number}; shift 2 ;;
    -h|--help) lab_usage; exit 0 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done

ENGINE=$(lab_engine 2>/dev/null || true)
PROBE="$ONMS_URL/opennms/rest/health/probe"
echo "Waiting for $PROBE (up to ${TIMEOUT}s) ..."
start=$SECONDS; next_report=0; stopped=0

container_state() {
  [ -n "$ENGINE" ] || return 0
  "$ENGINE" container inspect -f '{{.State.Status}}' "$HORIZON_CONTAINER" 2>/dev/null || echo "missing"
}

while :; do
  elapsed=$((SECONDS - start))
  body=$(curl -s --max-time 10 "$PROBE" 2>/dev/null)
  if [[ "$body" == *"Everything is awesome"* ]]; then
    echo "OpenNMS is ready after ${elapsed}s: $ONMS_URL/opennms/"
    exit 0
  fi

  # A container that keeps stopping will never answer: fail early and show why. (No container
  # with that name at all is fine: OpenNMS may run under another name, or elsewhere.)
  state=$(container_state)
  case "$state" in
    exited|stopped|dead)
      stopped=$((stopped + 1))
      if [ "$stopped" -ge 4 ]; then
        echo "Container $HORIZON_CONTAINER is $state. Its last log lines:" >&2
        "$ENGINE" logs --tail 40 "$HORIZON_CONTAINER" 2>&1 | sed 's/^/  | /' >&2
        exit 1
      fi ;;
    *) stopped=0 ;;
  esac

  if [ "$elapsed" -ge "$next_report" ]; then
    next_report=$((elapsed + 15))
    code=$(lab_http_status "$PROBE")
    case "$code" in
      000)
        hint=""
        if [ -n "$ENGINE" ] && [ "$state" = running ]; then
          hint=$("$ENGINE" logs --tail 1 "$HORIZON_CONTAINER" 2>&1 | tr -d '\r' | cut -c1-110)
          [ -n "$hint" ] && hint=" | last log line: $hint"
        fi
        echo "  ${elapsed}s  no answer yet (container: ${state:-?})$hint" ;;
      599)
        # the probe answers 599 until every health check is green; the JSON variant says which
        detail=$(lab_get /rest/health -H 'Accept: application/json' 2>/dev/null | python3 -c '
import json, sys
try:
    h = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
bad = [r for r in h.get("responses", []) if r.get("status") != "Success"]
print("; ".join("%s: %s" % (r.get("description"), r.get("status")) for r in bad[:3]) + (" ..." if len(bad) > 3 else ""))' 2>/dev/null)
        echo "  ${elapsed}s  starting, health checks not green yet${detail:+: $detail}" ;;
      *)
        echo "  ${elapsed}s  web app starting (HTTP $code from the probe)" ;;
    esac
  fi

  if [ "$elapsed" -ge "$TIMEOUT" ]; then
    echo "Timed out after ${TIMEOUT}s." >&2
    [ -n "$ENGINE" ] && echo "Look at: $ENGINE logs --tail 80 $HORIZON_CONTAINER   (and docs/09-troubleshooting.md)" >&2
    exit 1
  fi
  sleep 5
done
