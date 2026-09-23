# Shared UI assets for OpenNMS UI-extension plugins

Several OpenNMS UI plugins that show the same node icons should not each carry their own copy of
the images. This lab shows how to keep **one host folder** of assets that **every plugin reads**,
served by the **Jetty web server built into OpenNMS**, and explains in detail why it works.

Target: **OpenNMS Horizon 33.1.8** (Integration API 1.6.1, Jetty 9.4.57, Karaf 4.3.10, UI on Vue 3.3.7),
run with Podman or Docker.

## The three requirements, and where they are met

| Requirement | How | Where |
|---|---|---|
| 1. Share assets among all plugins without copying them into each plugin | Plugins ship only code. Images live once in `shared-assets/`, are served at `/opennms/assets/shared/`, and are found through `manifest.json` with a small shared helper. | `packages/shared-assets/`, `plugins/`, [Part 3](docs/03-how-plugins-find-assets.md) |
| 2. A host directory in the container deployment: drop a file in and the plugins find it | `./shared-assets` is bind-mounted read-only into the `opennms` web application. Jetty serves a new file on the next request, with no restart, rebuild or `podman exec`. | `compose.yml`, `scripts/assets.py`, [Part 2](docs/02-where-assets-live.md) |
| 3. A teaching guide: where assets are stored, how plugins find them, how Jetty serves them | Eight parts plus a source trace with a link to every file and line the explanations rely on. | [docs/](docs/README.md) |

## Quick start

```bash
podman-compose up -d                    # OpenNMS 33.1.8 + PostgreSQL, with ./shared-assets mounted
scripts/verify-assets.sh --live-drop    # prove Jetty serves the folder, including a live drop
scripts/build-plugins.sh                # build both demo plugins (npm + Maven) into overlay/deploy/
podman-compose restart horizon          # the entrypoint copies the KARs into deploy/
scripts/provision-demo-nodes.sh         # seven demo nodes for the icon rules
```

Then open <http://localhost:8980/opennms/ui/> (admin / admin) and use the **Plugins** menu. The full
walkthrough, including adding an icon while everything runs, is [Part 6](docs/06-lab-walkthrough.md).

## How it fits together

```text
host: ./shared-assets/ ──bind mount (ro)──► /usr/share/opennms/jetty-webapps/opennms/assets/shared/
                                                    │ served by the /opennms web app's DefaultServlet
                                                    ▼
browser:  /opennms/ui/  ── Node Inventory plugin ──┐
                        ── Icon Catalog plugin  ───┴─► GET /opennms/assets/shared/icons/router.svg?rev=1
                           (each ships only its JS: /opennms/rest/plugins/ui-extension/module/<id>)
```

Why this location: under `/opennms/assets/` the files are on the UI's own origin (so the UI's
Content-Security-Policy allows them), readable without extra configuration (Spring Security permits
`/assets/**`), cached for an hour (OpenNMS's `no-store` rule exempts `assets/`), and served by a
servlet that re-checks the disk on every request. [Part 4](docs/04-how-jetty-serves-them.md) traces a
request through every layer, and [Part 5](docs/05-design-decisions.md) compares four alternatives,
including a login-protected variant.

## Repository map

```text
compose.yml, .env.example     OpenNMS 33.1.8 + PostgreSQL; the shared-folder mount is the key line
shared-assets/                THE shared folder: manifest.json (+ schema), icons/, branding/
packages/shared-assets/       @onms-lab/shared-assets: URL building, catalog loading, node-icon rules (+ tests)
plugins/node-inventory/       demo plugin 1: node table with shared icons (Java + blueprint + Vite + KAR)
plugins/icon-catalog/         demo plugin 2: the catalog, with the HTTP headers Jetty sends, and a probe box
plugins/pom.xml               builds both plugins
overlay/                      copied into $OPENNMS_HOME at start; build-plugins.sh puts the KARs in overlay/deploy/
scripts/assets.py             add / validate / list / bump for the shared folder (atomic, permission-safe)
scripts/verify-assets.sh      receiver-side HTTP checks against a running OpenNMS
scripts/check_plugins.py      checks any UI-extension bundle against the rules of the 33.1.8 plugin loader
scripts/build-plugins.sh      npm + contract check + Maven, copies the KARs to overlay/deploy/
scripts/provision-demo-nodes.sh  demo requisition that exercises every icon rule
scripts/validate-repo.sh      offline sweep: JSON, XML, compose, scripts, folder, plugin contract, tests, lint
tests/e2e/                    Playwright test: both plugins render the same files, one manifest fetch, no CSP errors
docs/                         the teaching guide (start at docs/README.md)
```

## What was verified

The source of OpenNMS 33.1.8, OIA 1.6.1, Jetty 9.4.57 and Karaf 4.3.10 was read for every claim
([source trace](docs/reference/source-trace.md)). Serving behaviour, the plugin loader and both demo
plugins were exercised in a test harness built from OpenNMS's own `jetty.xml` and `web.xml`, with
Chromium. The real container and the Maven/KAR build could not be run where this was written;
[verification](docs/reference/verification.md) lists exactly what was and was not tested, and
`scripts/verify-assets.sh` plus `tests/e2e` close the gap on your machine.

## Requirements

Podman 4+ with podman-compose (or Docker with Compose), Python 3, curl. For building the plugins:
Node.js 18.18+ with npm, JDK 11+ and Maven 3.8+. About 4 GB of memory for the containers.
