#!/usr/bin/env bash
# Run a Karaf shell command in the running OpenNMS, or open the Karaf shell.
#
#   scripts/karaf.sh                                   # interactive shell (logout or Ctrl-D to leave)
#   scripts/karaf.sh kar:list
#   scripts/karaf.sh 'feature:list -i | grep opennms-lab'
#
# Logs in over SSH on 127.0.0.1:ONMS_KARAF_SSH_PORT (8101) as ONMS_USER. OpenNMS replaces Karaf's
# "karaf" login realm with its own user database, so this is the web UI's admin account and password.
# With sshpass installed, ONMS_PASS from .env is sent for you; otherwise ssh asks for it.
# Karaf's host key lives in etc/ and changes whenever the etc volume is re-created, so host key
# checking is switched off for this port, which is only published on 127.0.0.1.
set -euo pipefail
# shellcheck source=scripts/lib.sh
. "$(dirname "$0")/lib.sh"

SSH=(ssh -p "${ONMS_KARAF_SSH_PORT:-8101}" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR)
[ $# -eq 0 ] && SSH+=(-t)
if command -v sshpass >/dev/null 2>&1; then
  export SSHPASS=$ONMS_PASS
  exec sshpass -e "${SSH[@]}" "$ONMS_USER@localhost" "$@"
fi
exec "${SSH[@]}" "$ONMS_USER@localhost" "$@"
