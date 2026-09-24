#!/usr/bin/env bash
# Import a small requisition whose nodes exercise every rule in shared-assets/manifest.json.
# The addresses are in 192.0.2.0/24 (TEST-NET-1, RFC 5737): nothing answers, and with an
# empty foreign-source definition (no detectors) OpenNMS does not even try to scan them.
#
#   scripts/provision-demo-nodes.sh            # login and URL from .env (scripts/lib.sh)
set -euo pipefail
# shellcheck source=scripts/lib.sh
. "$(dirname "$0")/lib.sh"
AUTH="$ONMS_USER:$ONMS_PASS"
FS=${FOREIGN_SOURCE:-SharedAssetsLab}
lab_check_login || exit 1

curl -fsS -u "$AUTH" -H 'Content-Type: application/xml' -X POST \
  "$ONMS_URL/opennms/rest/foreignSources" --data-binary @- <<XML
<foreign-source xmlns="http://xmlns.opennms.org/xsd/config/foreign-source" name="$FS">
  <scan-interval>1d</scan-interval>
  <detectors/>
  <policies/>
</foreign-source>
XML
echo "foreign source '$FS' defined (no detectors, no policies)"

req_node() { # foreign-id ip [category]
  printf '  <node foreign-id="%s" node-label="%s">\n    <interface ip-addr="%s" status="1" snmp-primary="N"/>\n' "$1" "$1" "$2"
  [ -n "${3:-}" ] && printf '    <category name="%s"/>\n' "$3"
  printf '  </node>\n'
}
{
  echo "<model-import xmlns=\"http://xmlns.opennms.org/xsd/config/model-import\" foreign-source=\"$FS\">"
  req_node core-router-01   192.0.2.1  Routers
  req_node access-switch-01 192.0.2.2  Switches
  req_node edge-fw-01       192.0.2.3  Firewalls
  req_node ap-lobby-01      192.0.2.4  AccessPoints
  req_node raspberry-pi-01  192.0.2.5
  req_node db-01            192.0.2.6  Servers
  req_node mystery-box      192.0.2.7
  echo "</model-import>"
} | curl -fsS -u "$AUTH" -H 'Content-Type: application/xml' -X POST \
      "$ONMS_URL/opennms/rest/requisitions" --data-binary @-
echo "requisition '$FS' stored"

curl -fsS -u "$AUTH" -X PUT "$ONMS_URL/opennms/rest/requisitions/$FS/import?rescanExisting=false"
echo "import of '$FS' requested; nodes appear within a few seconds"
echo "sysObjectID rules (e.g. 'linux') only match real SNMP nodes, such as a Raspberry Pi running net-snmp."
