# Reference: what was verified, and how

This guide was written without access to a running OpenNMS container: the build environment
could not pull images from Docker Hub or artifacts from Maven Central. Everything that could be
checked without them was checked against the real code, and the installation and deployment
tooling was run with stand-ins for the two images. This page says what was checked, how, and what
is left for you to confirm in the lab.

## The test harness

The harness reproduces the parts of OpenNMS that decide how a static file and a plugin module are
served, using OpenNMS's own configuration files:

| Piece | In OpenNMS 33.1.8 | In the harness |
|---|---|---|
| Web server | Jetty 9.4.57, configured by `JettyServer` from `jetty.xml` | Jetty 9.4.53 (Ubuntu `libjetty9-java`), configured the same way from **OpenNMS's `jetty.xml`** |
| `MDCHandler` | sets the logging prefix | replaced by a plain `HandlerWrapper` |
| `OpenNMSWebAppProvider` | `WebAppProvider` + JSP setup + `ApproveAbsolutePathAliases` | `WebAppProvider` + **OpenNMS's `ApproveAbsolutePathAliases`** (compiled from source), no JSP |
| `/opennms` web application | full OpenNMS webapp | a directory with the **`default` servlet definition copied verbatim** from OpenNMS's `web.xml`, plus the CSP and `nosniff` headers with OpenNMS's values |
| Spring Security | `/assets/**` anonymous, `/**` `ROLE_USER` | not emulated (read from the configuration only) |
| Shared folder | bind mount, read-only | `mount --bind` of a host directory, remounted read-only |
| `/opennms/rest/plugins/...` | `UIExtensionServiceImpl` in Karaf | a servlet that reproduces its logic: blueprint `<property>` values to a registry, `classLoader.getResource(path)` per plugin JAR, `new String(bytes)`, same content types |
| `/opennms/ui/` | Vue 3.3.7 app that loads plugins | a page with Vue 3.3.7, Pinia 2.1.7, vue-router 4.2.5 on `window` and the loader logic copied from `ui/src/main.ts` and `ui/src/components/Plugin/utils.ts` |
| `/opennms/api/v2/nodes` | REST v2 | a static JSON file with eight nodes |

The Jetty classes the guide depends on (`ResourceService`, `CachedContentFactory`, the alias
checkers, `HeaderRegexRule`, the scanner) were compared in the 9.4.57 source; where this page
quotes a harness result for them, the 9.4.57 code takes the same path.

## HTTP behaviour (curl against the harness)

| # | Check | Result |
|---|---|---|
| 1 | `GET /opennms/assets/shared/icons/router.svg` | `200`, `image/svg+xml`, `Cache-Control: max-age=3600,public`, no `Pragma`, CSP and `nosniff` present |
| 2 | same file type at `/opennms/images/example.svg` | `200`, `Cache-Control: no-store`, `Pragma: no-cache` |
| 3 | `manifest.json` | `200`, `application/json`, `max-age=3600,public` |
| 4 | PNG download | `image/png`, byte-identical (MD5 of source and download match) |
| 5 | `icons/`, `icons`, `/` of the folder | `403`, `302` to `icons/`, `403` |
| 6 | `If-Modified-Since` with the `Last-Modified` value | `304` |
| 7 | `Range: bytes=0-9` | `206`, 10 bytes |
| 8 | `../WEB-INF/web.xml`, `%2e%2e/...`, `..%2f...`, `/WEB-INF/web.xml` | `404` for all |
| 9 | a file that does not exist | `404` |
| 10 | new file written on the host (temporary name, then `mv`) | `404` before, `200 image/svg+xml` on the request right after |
| 11 | the file replaced (temporary name, then `mv`) | new content and new `Last-Modified` on the next request |
| 12 | the file deleted | `404` on the next request |
| 13 | `server.svg.gz` next to `server.svg`, `Accept-Encoding: gzip` | `Content-Encoding: gzip`, `Vary: Accept-Encoding` |
| 14 | symlinks in the folder: relative in-folder link / link to an existing outside file / dangling link | `200` / `200` / empty reply (`IllegalArgumentException: unknown content` in `ResourceService.sendData`) |
| 15 | the whole folder as a symlink instead of a bind mount | `200` |
| 16 | a PNG requested through the module endpoint | labelled `application/javascript;charset=utf-8`; 9,737 bytes in, 17,490 bytes out |
| 17 | directory mounted in `jetty-webapps/` (option D) | context deployed after about 15 s; no `Cache-Control`; directory listing `200`; top-level file added: context stopped and restarted about 20 s later; file added in a sub-directory: no redeploy |
| 18 | extra context in `jetty.xml` (option C) | weak `ETag`, `Cache-Control: no-cache`, `304` on `If-None-Match`, `403` for directories, `/opennms` unaffected |
| 19 | handler chain built from OpenNMS's `jetty.xml` | `HandlerWrapper(MDCHandler) -> HandlerCollection [RewriteHandler, ContextHandlerCollection, DefaultHandler]` |
| 20 | `scripts/verify-assets.sh --live-drop --plugins` | 20 passed, 1 warning (a probe plugin without `style.css`), 0 failed |

## Containers and compose file (Podman and Docker, with stand-in images)

The images `postgres:15` and `opennms/horizon:33.1.8` could not be pulled. Two small stand-in
images took their place, built from BusyBox: the PostgreSQL stand-in answers `pg_isready` after a
few seconds and accepts TCP connections on 5432; the Horizon stand-in has the same user (`opennms`,
uid 10001, gid 10001, created the same way), the same `/opt/opennms` symlink, volumes and
directories, and an entrypoint with the same flags and order of steps as the real one
(`etc-pristine` when `etc/` is empty, datasource file from the environment, etc overlay copied,
installer skipped when `etc/configured` exists, then a web server on 8980 that serves
`jetty-webapps/`). It also reports its uid/gid, `ping_group_range` and the mounts at start. The
stand-ins were switched in through `HORIZON_IMAGE` and `POSTGRES_IMAGE` in `.env`; `compose.yml`
itself was used unchanged. Podman 4.9.3 (rootful, netavark, runc), podman-compose 1.6.0, Docker
29.4.3 with Compose v5.1.3.

| # | Check | Result |
|---|---|---|
| 1 | `podman-compose up -d` on empty volumes | the database started first; podman-compose ran `podman wait --condition=healthy` and started Horizon only once the database was healthy (after 9 s) |
| 2 | `podman-compose run --rm horizon -i` (and `docker compose run --rm horizon -i`) | started the database first and waited until it was healthy; resolved `database` by name, reached port 5432, copied the etc overlay, wrote `etc/configured` into the `onms-etc` volume, exited 0; the one-off container was removed |
| 3 | the Horizon process | `uid=10001(opennms) gid=10001(opennms)`, `ping_group_range` = `10001 10001` |
| 4 | the three bind mounts | shared folder readable by uid 10001; `/opt/opennms-lab-deploy` read-only; `etc/org.apache.felix.fileinstall-lab.cfg` present after start |
| 5 | ports | published on `127.0.0.1` only: reachable there, not through the host's own address; with `ONMS_HTTP_BIND=0.0.0.0` podman-compose re-created the container and the port answered on the host address |
| 6 | health check with a `curl` stand-in | container `healthy`; `scripts/wait-for-opennms.sh` and `scripts/lab-status.sh` saw it |
| 7 | `stop_grace_period: 1m` | podman-compose passes it as `podman stop -t 60` on `stop`/`down`/`restart` (the container's own stop timeout stays 10 s, hence the hint in Part 0); Docker Compose stores `StopTimeout=60` in the container |
| 8 | Day 2 commands of Part 0.11 | `restart horizon`, `stop`/`start`, removing `etc/configured` then re-creating (the installer ran again), `podman volume export`, `down -v` |
| 9 | the by-hand commands of Part 0.12, taken verbatim from the Markdown (only image names and ports replaced) | ran with Podman and, with `podman` replaced by `docker`, with Docker: env file values with spaces kept literally, `StopTimeout=60`, health check, sysctl, read-only mounts |
| 10 | switching from the by-hand installation to compose (Part 0.12) | podman-compose reused the network and volumes (`System is already configured`); Docker Compose refused the network it had not created, and continued with the same volumes once the network was removed |
| 11 | default `ping_group_range` without the sysctl | Podman: `0 0` (from `default_sysctls` in `containers.conf`); Docker: `0 2147483647` |
| 12 | `depends_on: condition: service_healthy` in older podman-compose releases | absent from the released sources of 1.0.6, 1.1.0 and 1.2.0, present from 1.3.0 |
| 13 | the image's `/health.sh` (`curl -sSF <url>`) | curl 8.5 rejects the arguments (`option -sSF: is badly used here`, exit 2), so the lab uses its own check |

## Plugin deployment tooling

The deploy scripts need a Karaf that installs KARs and a REST API that lists UI extensions. They
were run against a stand-in (Python) that implements what the scripts depend on, as read in the
Karaf 4.3.10 and Felix FileInstall 3.7.4 sources: a watcher on `./deploy` that polls every
second with the filter `.*[.]kar` (whole-name match) and a checksum of modification time and size;
new file = install, changed file = uninstall + install, deleted file = uninstall; a KAR name that is
already installed is skipped; `Karaf-Feature-Start: false` adds nothing to the registry until a
`feature:install`; the registry is keyed by extension id; `/rest/plugins`, the module and CSS
endpoints, `/rest/info`, `/rest/health` and the anonymous probe with basic authentication. The
KARs were built with the layout of `karaf-maven-plugin`'s `kar` goal (from `KarMojo`'s source):
manifest, `repository/.../*-features.xml` with classifier `features`, the bundle JAR with the
demo plugin's real `blueprint.xml`, built module, `style.css` and the class compiled with `javac`.

| # | Scenario | Result |
|---|---|---|
| 1 | `deploy-plugin.sh node-inventory`, then `icon-catalog` | contract check passed; copied as `.<name>.part` then renamed; live after about 4 s each; `lab-status.sh` shows both registered |
| 2 | the same KAR again | "already this exact build", confirmed live at once |
| 3 | a new build (module changed) under the same file name | reported as update; the script waited until the served module's SHA-256 matched the new build, not just until the id was listed |
| 4 | the same plugin under another file name (`node-inventory-1.0.1.kar`) | refused, naming the feature and extension id already deployed |
| 5 | the same with `--replace` | old KAR undeployed and gone from `/rest/plugins`, new one deployed and live |
| 6 | `undeploy-plugin.sh` by plugin name and by file name; an unknown name | removed and confirmed gone; unknown name lists what is deployed |
| 7 | a KAR with `Karaf-Feature-Start: false` | deployed, prints the `feature:install` command instead of waiting; registered after the (simulated) `feature:install` |
| 8 | a KAR whose module does not assign `window[extensionId]` | refused by the contract check; deployed with `--force` |
| 9 | wrong password in `.env` | KAR copied, the script explains that only the live check was skipped, exit 1 |
| 10 | OpenNMS not running | deploy and undeploy only change the folder and say so, exit 0; `wait-for-opennms.sh` times out with a hint |
| 11 | `wait-for-opennms.sh` while the probe answers 599 | prints the health check that is not green, then "ready" when it turns green |
| 12 | `verify-assets.sh --live-drop --plugins` | 20 passed, 0 failed |
| 13 | `karaf.sh` with and without `sshpass` (ssh replaced by a recorder) | builds `ssh -p 8101 ... admin@localhost <command>`, adds `-t` for the interactive shell, passes the password only through `SSHPASS` |

`tests/scripts/test_tools.py` keeps the core of this as unit tests: `kar_info` on generated KARs
(name, `Karaf-Feature-Start` semantics, features repository URI, module hash, conflicts),
`check_plugins.py` on KARs, and `.env` parsing in `scripts/lib.sh` (11 tests, all pass). The
Playwright configuration reads `.env` the same way (checked with a probe test: values from the file,
quotes stripped, environment wins).

## Browser behaviour (Chromium through Playwright, against the harness)

| # | Check | Result |
|---|---|---|
| 1 | Node Inventory: every shared image decoded (`naturalWidth > 0`) | pass, 10 images |
| 2 | Node Inventory: image URLs are `/opennms/assets/shared/...?rev=N` | pass |
| 3 | Node Inventory: rule results (nms for the `selfmonitor` node, router, switch, firewall, wifi-ap, sbc, linux, server, unknown) | pass |
| 4 | Icon Catalog: every catalog image decoded | pass, 10 images |
| 5 | Icon Catalog: `HEAD` shows `Cache-Control: max-age=3600,public` | pass |
| 6 | both plugins in one page session caused one `manifest.json` request | pass (1 request) |
| 7 | a file written on the host while the page is open is served and rendered (Probe box) | pass |
| 8 | images packed in a bundle, requested through `/rest/plugins/ui-extension/module/...` | fail to render, as expected (SVG and PNG) |
| 9 | an image from another origin (`127.0.0.1` vs `localhost`) | blocked by CSP `img-src` |
| 10 | revision bump in `manifest.json` then reload | every URL carries the new `?rev=` |
| 11 | CSP violations caused by the plugins | none |

The shipped Playwright test (`tests/e2e/shared-assets.spec.ts`) was also run against the harness,
with the login step skipped: 2 of 2 tests passed. All of this was repeated after the second version
of the lab added the `nms` icon and its rule.

## Build and static checks

| Check | Result |
|---|---|
| `@onms-lab/shared-assets` unit tests (Vitest 2.1.9) | 34 of 34 passed |
| type checks: `tsc` for the helper, `vue-tsc` 1.8.27 for both plugins | clean |
| Vite 5.4.21 builds of both modules | `nodeInventory.es.js` 9.5 kB, `iconCatalog.es.js` 10.2 kB, `style.css` each; ASCII only; no `process.env`; Vue used through `window.Vue` |
| Java: both `UIExtension` classes compiled with `javac --release 11` against the OIA 1.6.1 interface source | clean with `-Xlint:all` |
| `scripts/check_plugins.py` on both plugins | 0 FAIL, 0 WARN |
| `scripts/check_plugins.py` on a copy of Node Inventory built *without* the Vue externals | FAIL "bundles its own Vue runtime", as intended |
| `scripts/check_plugins.py` on the OIA 1.6.1 `sample` bundle | flags `RedPlugin.es.js` (assigns `window["RedPlugin"]`, extension id `samplePluginOne`) and the inlined logo |
| `scripts/build-plugins.sh --no-maven` from a clean copy (`npm ci` from the lock file) | tests, builds and contract check pass; rebuilt modules byte-identical to the committed ones |
| all 11 POMs read with Maven 3.9.11's strict model reader | clean; an offline `mvn validate` stops only at downloading `maven-bundle-plugin` and `karaf-maven-plugin` |
| both `blueprint.xml` files against the OSGi Blueprint 1.0.0 XSD (from Apache Aries) | valid |
| both `features.xml` files (after Maven filtering) against the Karaf features 1.4.0 XSD | valid |
| `docker compose config` and `podman-compose config` (1.6.0) on `compose.yml` | both parse it; defaults resolve as intended |
| `scripts/validate-repo.sh` (JSON, XML, compose, mount sources, the watcher `.cfg`, Python, unit tests, `shellcheck -x`, executable bits, shared folder, plugin contract, helper tests and types, markdownlint), run on a fresh unpacked copy of the delivered zip after `npm ci` | all checks passed; `build-plugins.sh --no-maven` there rebuilt both modules byte-identical to the committed ones |
| JSON Schema validation of `manifest.json`, `shellcheck` on the shell scripts, `tsc` on the Playwright spec, `markdownlint`, internal link check of all docs, rendering of every Mermaid diagram | clean |
| Vite library mode with a 49 KB PNG import | inlined as a `data:` URI (confirms Part 1) |
| Vite library mode with `url(/opennms/assets/shared/...)` in CSS | kept unchanged, with the "will remain unchanged to be resolved at runtime" notice |

## The architecture guide

The [architecture guide](../architecture/README.md) describes OpenNMS itself rather than the lab's
tooling, so it was checked differently:

| What | How |
|---|---|
| Every statement about the process, the daemons, Jetty, the web application, Karaf, Felix and the bridge | read in the source at the exact tags (OpenNMS `opennms-33.1.8-1`, Jetty `9.4.57.v20241219`, Karaf `4.3.10`, Felix framework `6.0.5`, FileInstall `3.7.4`); 100 rows of the [source trace](source-trace.md#architecture-guide-process-and-daemons) link each one to its line |
| Counts quoted in the text (32 services, 27 enabled; 100 boot features, 22 of Karaf's; 1,383 extra system packages, 183 `org.opennms.*`) | computed by script from `service-configuration.xml`, `org.apache.karaf.features.cfg` and `custom.properties` |
| The Karaf shell commands in the "see it in the lab" sections | each command and option looked up in the Karaf 4.3.10 source (`system:start-level`, `bundle:list -t`, `bundle:headers`, `bundle:diag`, `bundle:find-class`, `bundle:tree-show`, `package:exports -b -p`, `service:list`, `shell:threads --list`, `feature:list -i`, `feature:info`, `kar:list`, `config:list`) |
| The 16 diagrams | generated by `docs/architecture/images/make_diagrams.py`, rendered in Chromium with Arial-compatible and DejaVu Sans fonts and inspected, so labels fit with either; `validate-repo.sh` checks that the SVG files match the script |
| Links between the pages | `scripts/check_links.py` checks every relative link and heading anchor |

The outputs described in the "see it in the lab" sections were **not** captured from a running
Horizon container (see the top of this page); they are what the source says you will see. Treat a
difference as something to report, not as a problem with your lab.

## Not verified here: please confirm in your lab

1. **The real container.** Run `scripts/lab-status.sh`, `scripts/verify-assets.sh --live-drop --plugins`
   and the Playwright test in `tests/e2e` against the compose lab. They check the same things as
   the harness and the stand-ins, on the real stack. The first start's duration and log output,
   and the self-monitoring node (ICMP through the `ping_group_range` sysctl), could only be
   checked at the level of the kernel setting.
2. **The real Karaf deploy watcher.** That `etc/org.apache.felix.fileinstall-lab.cfg` creates a
   second watcher, and how the KAR deployer reacts to new, changed and deleted files, comes from the
   Karaf 4.3.10 and FileInstall 3.7.4 sources (the same mechanism as Karaf's own `deploy/`); the
   deploy scripts were run against a stand-in. Part 6.4 shows how to watch each layer in the real
   system.
3. **Spring Security.** The anonymous access to `/assets/**` and the roles for `/rest/**` come from
   reading `applicationContext-spring-security.xml`. `verify-assets.sh` checks the anonymous part
   (it sends no credentials for the shared files).
4. **The Maven/KAR build.** The POMs follow the OIA 1.6.1 `example-kar-plugin` archetype and the
   KAR module of the VeloCloud plugin (built by OpenNMS's CI), but they were not run here.
   `scripts/build-plugins.sh` runs them.
5. **The OSGi path.** Blueprint, `UIExtensionRegistryImpl`, the JAX-RS connector and the
   `ProxyFilter` were traced in the source and emulated in the harness, not executed. The Karaf
   commands in Part 6.4 show each layer in the real system.
6. **Podman specifics.** The containers here ran rootful; the `z` relabel option and rootless user
   mapping follow Podman's documented behaviour and were not exercised on an SELinux host or a
   Podman machine (macOS, Windows).
