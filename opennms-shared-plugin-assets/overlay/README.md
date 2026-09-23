# overlay

Mounted at `/opt/opennms-overlay`. At every start the container's entrypoint copies the contents of
this folder into `$OPENNMS_HOME` (`/usr/share/opennms`) with `rsync`, so this file ends up there too,
harmlessly.

`scripts/build-plugins.sh` writes the demo KARs to `overlay/deploy/`; after a restart they are in
`$OPENNMS_HOME/deploy/`, where Karaf installs them.

This is a copy made at start, not a live view. Never put files for `jetty-webapps/opennms/assets/shared/`
here: that path is the read-only mount of `shared-assets/`, the copy would fail and the container would
stop.
