# Changelog

## 2 - Installation guide and one-by-one plugin deployment

### Added

- **Part 0**: installing OpenNMS Horizon 33.1.8 and PostgreSQL 15 in containers, step by step, with
  `podman-compose` and, for comparison, with plain `podman run` commands; first login; checks; what
  lives where; day-2 operations (settings, opening the port, database passwords, upgrade, backup).
- **Part 6**: installing the plugins one by one, following each layer from the KAR file to the menu
  entry, then updating and removing a plugin, restarts and re-created containers, and your own KARs
  (including `Karaf-Feature-Start: false` and `etc/featuresBoot.d`).
- **A second Karaf deploy folder**: `./deploy` on the host, mounted at `/opt/opennms-lab-deploy` and
  watched through `etc-overlay/org.apache.felix.fileinstall-lab.cfg`. Copy a KAR in to install it,
  replace it to update, delete it to uninstall; no restart, and it survives re-created containers.
- Scripts: `deploy-plugin.sh`, `undeploy-plugin.sh`, `wait-for-opennms.sh`, `lab-status.sh`,
  `karaf.sh`, `kar_info.py`, and `lib.sh`, which gives all shell scripts the settings from `.env`.
- `check_plugins.py` also checks built KARs, and has `--quiet`.
- An `nms` icon with a `foreignSources` rule for OpenNMS's self-monitoring node (the rule type
  existed but no rule used it).
- Unit tests for the tooling (`tests/scripts/`) and three more helper tests.
- Part 5.6: the ways to get a KAR into a container, compared.

### Changed

- `compose.yml`: the web UI is published on `127.0.0.1` unless `ONMS_HTTP_BIND` says otherwise; the
  `net.ipv4.ping_group_range` sysctl lets OpenNMS ping under Podman; `stop_grace_period: 1m`;
  `restart: unless-stopped` for both services; image names configurable (`HORIZON_IMAGE`,
  `POSTGRES_IMAGE`); the `/opt/opennms-overlay` mount replaced by the etc overlay and the deploy
  folder.
- `.env.example`: passwords to change before the first start, the bind address, and the web login
  the scripts use (after the first-login password change, `admin`/`admin` no longer works).
- `build-plugins.sh` builds one plugin or all of them and no longer copies KARs anywhere.
- The Playwright configuration reads `.env` like the scripts.
- The guide is renumbered: the lab walkthrough became Part 6 (plugins) and Part 7 (the shared
  folder at runtime); migrating is Part 8; troubleshooting is Part 9, with new sections for
  installing and deploying.
- Part 2: the OpenNMS process runs as uid **and gid** 10001 (version 1 said group 0).

### Fixed

- `npm run typecheck` (and so `scripts/validate-repo.sh`) failed in a fresh clone: the plugins'
  type check needs the helper's type declarations, which only a build creates. It now builds the
  helper first.

### Removed

- `overlay/`. Deploying KARs through the overlay needed a restart to install a plugin and a
  re-created container to remove one, because the entrypoint copies the overlay but never deletes.

## 1 - Shared UI assets

One host folder of UI assets for all UI-extension plugins, served by OpenNMS's Jetty at
`/opennms/assets/shared/`; the shared helper; two demo plugins; the teaching guide (Parts 1 to 5);
the test harness verification.
