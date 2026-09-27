#!/usr/bin/env bash
# Install ONE plugin into the running OpenNMS: copy its KAR into ./deploy, which Karaf watches,
# then wait until OpenNMS serves exactly this build of the plugin's UI module.
#
#   scripts/deploy-plugin.sh node-inventory                 # a demo plugin (scripts/build-plugins.sh node-inventory first)
#   scripts/deploy-plugin.sh ~/src/my-plugin/assembly/kar/target/my-plugin.kar
#
# Options:
#   --timeout SEC   how long to wait for OpenNMS (default 180)
#   --no-wait       copy the KAR and return
#   --replace       first undeploy other KARs in ./deploy that ship the same features or extension ids
#   --force         deploy even when scripts/check_plugins.py reports a FAIL for the KAR
#
# Redeploying a new build of the same file name is an update: Karaf uninstalls the old KAR and
# installs the new one. The script knows the new build is live when the module OpenNMS serves has
# the same SHA-256 as the module inside the KAR.
set -euo pipefail
# shellcheck source=scripts/lib.sh
. "$(dirname "$0")/lib.sh"

TIMEOUT=180; WAIT=1; REPLACE=0; FORCE=0; ARG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --timeout) TIMEOUT=${2:?--timeout needs a number}; shift 2 ;;
    --no-wait) WAIT=0; shift ;;
    --replace) REPLACE=1; shift ;;
    --force) FORCE=1; shift ;;
    -h|--help) lab_usage; exit 0 ;;
    -*) echo "unknown option $1" >&2; exit 2 ;;
    *) [ -z "$ARG" ] || { echo "one plugin at a time" >&2; exit 2; }; ARG=$1; shift ;;
  esac
done
[ -n "$ARG" ] || { lab_usage; exit 2; }

DEPLOY_DIR="$REPO/deploy"
KARINFO=(python3 "$REPO/scripts/kar_info.py")

# --- 1. which KAR? ------------------------------------------------------------------------------
if [ -f "$ARG" ]; then
  KAR=$ARG
elif [ -f "$REPO/plugins/$ARG/assembly/kar/target/opennms-lab-$ARG-plugin.kar" ]; then
  KAR="$REPO/plugins/$ARG/assembly/kar/target/opennms-lab-$ARG-plugin.kar"
elif [ -d "$REPO/plugins/$ARG" ]; then
  echo "No KAR built for '$ARG' yet. Build it first:  scripts/build-plugins.sh $ARG" >&2; exit 1
else
  echo "'$ARG' is neither a .kar file nor a demo plugin (plugins/*)." >&2; exit 1
fi
case "$KAR" in *.kar) ;; *) echo "$KAR: Karaf only deploys files named *.kar from this folder" >&2; exit 1 ;; esac
NAME=$(basename "$KAR")
DEST="$DEPLOY_DIR/$NAME"

# --- 2. look inside, and check it like the OpenNMS UI will --------------------------------------
echo "== $NAME"
"${KARINFO[@]}" "$KAR" | sed 1d
FEATURE_START=$("${KARINFO[@]}" --get featureStart "$KAR")
EXTENSIONS=$("${KARINFO[@]}" --get extensions "$KAR")
if [ -n "$EXTENSIONS" ]; then
  echo; echo "== Contract check"
  if ! python3 "$REPO/scripts/check_plugins.py" --quiet "$KAR"; then
    if [ "$FORCE" = 1 ]; then echo "(--force: deploying anyway)"
    else echo "Not deployed. Fix the FAILs above, or pass --force to deploy anyway." >&2; exit 1; fi
  fi
fi

# --- 3. no second KAR with the same features / ids ----------------------------------------------
shopt -s nullglob
OTHERS=("$DEPLOY_DIR"/*.kar)
shopt -u nullglob
if [ ${#OTHERS[@]} -gt 0 ]; then
  set +e; CONFLICTS=$("${KARINFO[@]}" --conflicts "$KAR" "${OTHERS[@]}"); rc=$?; set -e
  if [ "$rc" = 3 ]; then
    echo; echo "Already deployed under another file name:"
    awk -F'\t' '{ n = $1; sub(/.*\//, "", n); print "  deploy/" n ": " $2 }' <<<"$CONFLICTS"
    if [ "$REPLACE" = 0 ]; then
      echo "Karaf would install both. Undeploy the old one first (scripts/undeploy-plugin.sh <file>), or use --replace." >&2
      exit 1
    fi
    cut -f1 <<<"$CONFLICTS" | sort -u | while read -r old; do
      "$REPO/scripts/undeploy-plugin.sh" --timeout "$TIMEOUT" "$old"
    done
  elif [ "$rc" != 0 ]; then
    echo "kar_info could not read one of the KARs in $DEPLOY_DIR" >&2; exit 1
  fi
fi

# --- 4. copy under a temporary name, then rename (Karaf only looks at *.kar) --------------------
echo
if [ -f "$DEST" ] && cmp -s "$KAR" "$DEST"; then
  echo "deploy/$NAME is already this exact build; nothing to copy."
else
  [ -f "$DEST" ] && action="update (Karaf uninstalls the old KAR, then installs this one)" || action="new install"
  TMP="$DEPLOY_DIR/.$NAME.part"
  cp "$KAR" "$TMP"
  chmod 0644 "$TMP"                  # the container reads it as uid 10001
  mv -f "$TMP" "$DEST"
  echo "Copied to deploy/$NAME: $action."
fi

if [ "$FEATURE_START" = false ]; then
  echo
  echo "This KAR has 'Karaf-Feature-Start: false': Karaf adds its features but installs none of them."
  echo "Install them in the Karaf shell (it asks for the OpenNMS admin password unless sshpass is installed):"
  "${KARINFO[@]}" --get features "$KAR" | sed 's|/.*||' | while read -r f; do
    echo "  scripts/karaf.sh feature:install $f"
  done
  echo "To keep them installed when the container is re-created, list them in etc/featuresBoot.d/"
  echo "(docs/06-installing-the-plugins.md, section 6.7)."
  exit 0
fi
[ "$WAIT" = 1 ] || exit 0
if [ -z "$EXTENSIONS" ]; then
  echo "The KAR has no UI extension to wait for; check it with scripts/karaf.sh kar:list and feature:list."
  exit 0
fi

# --- 5. wait until OpenNMS serves this build ----------------------------------------------------
set +e; lab_check_login; rc=$?; set -e
case "$rc" in
  0) ;;
  2) echo "Karaf installs the KAR when OpenNMS (re)starts; it stays in ./deploy until you remove it."; exit 0 ;;
  3) echo "The KAR is in ./deploy and Karaf installs it anyway; only the check that it went live was skipped." >&2; exit 1 ;;
  *) echo "Waiting anyway..." ;;
esac

echo "Waiting for OpenNMS to serve it (up to ${TIMEOUT}s) ..."
start=$SECONDS
pending=$EXTENSIONS
while :; do
  registered=$(lab_extensions)
  still=""
  while read -r id root module sha; do
    [ -z "$id" ] && continue
    if lab_has_extension "$id" <<<"$registered" && [ "$(lab_module_sha256 "$id" "$root" "$module")" = "$sha" ]; then
      continue
    fi
    still+="$id $root $module $sha"$'\n'
  done <<<"$pending"
  pending=$still
  [ -z "${pending//[$'\n']/}" ] && break
  if [ $((SECONDS - start)) -ge "$TIMEOUT" ]; then
    echo "Timed out. Still not live: $(awk '{print $1}' <<<"$pending" | paste -sd, -)" >&2
    echo "Look at Karaf's log:  $(lab_engine 2>/dev/null || echo podman) exec $HORIZON_CONTAINER tail -n 60 /usr/share/opennms/logs/karaf.log" >&2
    echo "and in the Karaf shell: scripts/karaf.sh kar:list, feature:list -i, bundle:list (docs/09-troubleshooting.md)" >&2
    exit 1
  fi
  sleep 2
done

echo "Live after $((SECONDS - start))s:"
while read -r id root module _; do
  [ -z "$id" ] && continue
  echo "  $id  ->  $ONMS_URL/opennms/ui/#/plugins/$id/$root/$module"
done <<<"$EXTENSIONS"
