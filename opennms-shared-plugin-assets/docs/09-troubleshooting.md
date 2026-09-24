# Part 9 - Troubleshooting

Work from the outside in: first the containers, then the plugin deployment, then the file on the
host, the HTTP response, and the plugin in the browser. The tools, in that order:
`scripts/lab-status.sh` shows the whole lab on one screen, `scripts/wait-for-opennms.sh` shows what
a starting OpenNMS waits for, `scripts/kar_info.py` and `scripts/check_plugins.py` look inside a
KAR, `scripts/assets.py validate` checks the shared folder, and `scripts/verify-assets.sh` checks
what Jetty answers.

Two log sources matter: `podman logs onms-shared-assets-horizon` for the container's entrypoint,
and the files in `/usr/share/opennms/logs/` inside the container for OpenNMS itself
(`karaf.log` for plugins, `manager.log` for the start-up of the daemons):

```bash
podman exec onms-shared-assets-horizon tail -n 80 /usr/share/opennms/logs/karaf.log
```

## Installing and starting

| Symptom | Likely cause | Fix |
|---|---|---|
| `podman-compose up` or `run` hangs at `podman wait --condition=healthy`; `podman ps` shows the database `(starting)` for ever | Podman runs health checks from systemd timers, and there is no systemd (WSL without systemd, a container inside a container) | enable systemd (WSL: `[boot] systemd=true` in `/etc/wsl.conf`, then `wsl --shutdown`); or run `podman healthcheck run onms-shared-assets-db` once by hand; or use Docker |
| OpenNMS starts before the database is ready, fails, and is restarted | podman-compose older than 1.3 ignores `condition: service_healthy` | harmless thanks to `restart: unless-stopped`; upgrade podman-compose to get a clean start |
| The installer fails with `password authentication failed for user "postgres"` | `POSTGRES_PASSWORD` in `.env` is not the one the database volume was created with | put the original password back, or start over with `podman-compose down -v` (deletes the database) |
| `password authentication failed for user "opennms"` after editing `OPENNMS_DBPASS` | the database user keeps its old password | change it in the database first ([Part 0.11](00-install-opennms-and-postgresql.md#011-day-2-stop-change-upgrade-back-up-remove)) |
| The Horizon container restarts again and again | the entrypoint exits with an error: database login, or the configuration tester rejecting a file (for example one you put in `etc-overlay/`) | `podman logs --tail 80 onms-shared-assets-horizon`; the last lines name the problem |
| A start error mentions `net.ipv4.ping_group_range` | the runtime refuses the sysctl (it needs the container's own network namespace, and groups that exist in it) | remove the two `sysctls:` lines; OpenNMS runs, only ICMP (discovery, ping monitoring) is affected |
| A start error mentions a missing bind-mount source such as `deploy` or `etc-overlay` | the folder was deleted or the command runs from another directory | run compose from the repository root; `mkdir -p deploy etc-overlay` |
| `lsetxattr ... operation not supported` or a relabel error at start (macOS, Windows) | the `z` option asks for an SELinux relabel of a folder shared from the host OS | remove `,z` from the three bind mounts |
| Port `8980` already in use | another OpenNMS or web server | set another `ONMS_HTTP_PORT` in `.env` |
| The container is killed (exit code 137), or OpenNMS is very slow | not enough memory for the Java heap plus PostgreSQL (on macOS: the Podman VM) | give the VM more memory (`podman machine set --memory 6144` while it is stopped), or lower `JAVA_OPTS` |
| `wait-for-opennms.sh` keeps printing "health checks not green" | a daemon failed to start, or a `featuresBoot.d` entry waits for a KAR that is not deployed | the listed check names the part; `curl -u admin:YOUR-PASSWORD http://localhost:8980/opennms/rest/health` shows all checks; see [Part 6.10](06-installing-the-plugins.md#610-your-own-plugins) for `wait-for-kar` |
| The web UI is not reachable from another machine | `ONMS_HTTP_BIND=127.0.0.1` (the default) | set `ONMS_HTTP_BIND=0.0.0.0` and run `podman-compose up -d` ([Part 0.11](00-install-opennms-and-postgresql.md#011-day-2-stop-change-upgrade-back-up-remove)) |
| The self-monitoring node never appears | ICMP is not allowed for group 10001 in the container | `podman exec onms-shared-assets-horizon cat /proc/sys/net/ipv4/ping_group_range` must include `10001`; keep the `sysctls:` lines |
| A script says `OpenNMS refused the login 'admin' (HTTP 401)` | the admin password changed and `.env` still has the old one | set `ONMS_PASS` in `.env` |

## Deploying plugins

Find the first layer of [Part 6.1](06-installing-the-plugins.md#61-how-a-kar-in-deploy-becomes-a-menu-entry)
that does not show your plugin; the cause is between it and the layer before.

| Symptom | Likely cause | Fix |
|---|---|---|
| `deploy-plugin.sh` times out and `karaf.log` says nothing about the KAR | the second deploy watcher does not exist: `etc-overlay/` not mounted, or the container was created before you added the file | `scripts/karaf.sh 'config:list "(felix.fileinstall.dir=/opt/opennms-lab-deploy)"'` must show one configuration; `podman-compose up -d` re-creates a container whose mounts changed |
| The watcher exists, still nothing happens | the file is not readable by uid 10001, or its name does not end in `.kar` | `chmod 644 deploy/*.kar` (the script does it); the filter ignores other names on purpose |
| `karaf.log`: `KAR ... is already installed. Please uninstall it first.` | a KAR with the same name is installed already, for example one copied into `$OPENNMS_HOME/deploy` or installed with `kar:install` | remove the other copy or run `kar:uninstall <name>` in the Karaf shell |
| `kar:list` shows the KAR, `feature:list -i` does not show its feature | `Karaf-Feature-Start: false` in the KAR, or `install="manual"` on the feature, or the installation failed (`Unable to install Kar feature` in `karaf.log`) | `scripts/karaf.sh feature:install <feature>`; for a failure, read the exception below that line |
| The feature is installed, the bundle is not `Active` | an import cannot be resolved (for example a bundle built against another Integration API version), or a blueprint error | `scripts/karaf.sh 'bundle:diag <id>'`; rebuild with the Integration API of your OpenNMS (`OIA_VERSION=...`) |
| The bundle is `Active`, `/rest/plugins` does not list the plugin | blueprint did not register a `UIExtension` service (wrong interface name, bean error), or another plugin uses the same `extensionId` and replaced it | `service:list org.opennms.integration.api.v1.ui.UIExtension`; `scripts/check_plugins.py <kar>` |
| `/rest/plugins` lists it, the **Plugins** menu does not | the UI page was loaded before the plugin was deployed | reload the page |
| `deploy-plugin.sh` refuses: "Already deployed under another file name" | a KAR with the same features or extension id sits in `./deploy` under another name (typically a version number in the file name) | `scripts/undeploy-plugin.sh <old file>`, or `--replace` |
| `deploy-plugin.sh` refuses because of a contract FAIL | the KAR would load but not work in the UI | fix what `check_plugins.py` reports, or `--force` to deploy anyway |
| A plugin is gone after `podman-compose down` / `up -d` | it was installed by hand in the Karaf shell, which only lives in `data/` | put its KAR into `./deploy`; for `Karaf-Feature-Start: false`, add a `featuresBoot.d` entry ([Part 6.10](06-installing-the-plugins.md#610-your-own-plugins)) |
| A removed plugin comes back after a restart | its KAR is still in `$OPENNMS_HOME/deploy` or in `./deploy` | remove the file from the folder, not only in the Karaf shell |

## The shared folder

| Symptom | Likely cause | Fix |
|---|---|---|
| Every shared URL returns `404` | the folder is not mounted where Jetty looks | the target must be `/usr/share/opennms/jetty-webapps/opennms/assets/shared`; check with `podman exec <container> ls /usr/share/opennms/jetty-webapps/opennms/assets/shared` |
| One file returns `404`, it exists on the host | file not readable by uid 10001, or it sits in a directory without `o+x` | `chmod 644` the file, `chmod 755` the directories; `assets.py validate` lists them |
| `ls` inside the container says "Permission denied" | SELinux label | add `z` to the mount options (already in `compose.yml`) |
| The folder listing returns `403` | `dirAllowed=false` in OpenNMS's `web.xml` | expected; use `manifest.json` |
| A symlinked file gives an empty reply or `404` | the link target does not exist inside the container | copy the file instead of linking it |
| The container stops at start with an `rsync` error | you added an `/opt/opennms-overlay` mount that contains files for `jetty-webapps/opennms/assets/shared/`, which is a read-only mount | keep shared files out of any overlay; the shared folder has its own mount |
| A file shows up broken (half an image) | it was written in place while being served | write to a temporary name and rename, as `assets.py add` does |

## The HTTP response

| Symptom | Likely cause | Fix |
|---|---|---|
| The old version of a replaced icon keeps showing | the browser's cache (`max-age=3600`) | `python3 scripts/assets.py bump` and reload |
| `Cache-Control: no-store` on a shared file | the file is served from outside `/opennms/assets/` (option B), or a custom `etc/jetty.xml` changed the rule | mount under `assets/`, or accept `no-store` |
| An SVG downloads instead of displaying when opened directly | wrong extension, so no `image/svg+xml` type | files need a known extension (`.svg`, `.png`, `.webp`, ...) |
| `401`/`302` to the login page for a shared file | the folder is mounted outside `/assets/` and you are not logged in | expected for option B; for option A check the URL |

## The plugin in the browser

| Symptom | Likely cause | Fix |
|---|---|---|
| The plugin is missing from the **Plugins** menu and from `/opennms/rest/plugins` | see [Deploying plugins](#deploying-plugins) | follow the layers of Part 6.1 |
| Two plugins, one menu entry | both use the same `extensionId` | ids must be unique; `check_plugins.py` checks this across the plugins you pass it |
| Console: "Errors with component url." | `moduleFileName` without `.es`, or a `resourceRootPath` containing `/` | see Part 3 and `check_plugins.py` |
| The page stays empty, no console error | the module assigns a different `window[...]` key than the loader reads | `window[extensionId] = Component` (legacy plugins excepted) |
| `ReferenceError: process is not defined` | library mode left `process.env.NODE_ENV` in the module | `define: { 'process.env.NODE_ENV': JSON.stringify('production') }` in `vite.config.ts` |
| Vue warnings about invalid vnodes, or reactivity that never updates | the module bundles its own Vue | externalise `vue`, `pinia`, `vue-router` to the `window` globals |
| Text with `?` or garbage characters | non-ASCII characters in the module, decoded with the JVM default charset | keep the module ASCII-only; `check_plugins.py` warns |
| Console: "Refused to load the image ... Content Security Policy" | the image URL has another origin (host name, port or scheme) | use root-relative URLs (`/opennms/assets/shared/...`), which the helper builds |
| All icons show the default icon | `manifest.json` not loaded (network error, invalid JSON) | open it in the browser; the helper logs `[shared-assets] manifest unavailable` |
| The plugin module is re-downloaded on every page load | `/opennms/rest/...` responses carry `Cache-Control: no-store` | expected; that is OpenNMS's policy for everything outside `/opennms/assets/` |
