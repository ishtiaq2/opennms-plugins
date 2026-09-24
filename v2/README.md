# Shared UI assets for OpenNMS UI-extension plugins

Several OpenNMS UI plugins that show the same node icons should not each carry their own copy of
the images. This lab shows how to keep **one host folder** of assets that **every plugin reads**,
served by the **Jetty web server built into OpenNMS**, and explains in detail why it works. It also
takes you through the whole installation: **OpenNMS and PostgreSQL in containers**, then the
**plugins one by one**, each installed by dropping its KAR into a second host folder. A separate
**architecture guide** opens up OpenNMS itself, step by step and with a diagram per step: the one
JVM, the daemons, Jetty, Karaf, Felix, bundles and plugins, and how they work together.

Target: **OpenNMS Horizon 33.1.8** (Integration API 1.6.1, Jetty 9.4.57, Karaf 4.3.10, UI on Vue 3.3.7)
with **PostgreSQL 15**, run with Podman (rootless) or Docker.

## What the lab gives you

| Requirement | How | Where |
|---|---|---|
| Install OpenNMS and PostgreSQL in containers, step by step | `compose.yml` with health-gated start-up, passwords in `.env`, the web UI on `127.0.0.1` until you open it; the same with plain `podman run` for comparison | [Part 0](docs/00-install-opennms-and-postgresql.md), `compose.yml` |
| Install the plugins one by one | `./deploy` is watched by Karaf: copy a KAR in = install, replace = update, delete = uninstall, no restart. Scripts check each KAR first and wait until OpenNMS serves it. | [Part 6](docs/06-installing-the-plugins.md), `scripts/deploy-plugin.sh` |
| Share assets among all plugins without copying them into each plugin | Plugins ship only code. Images live once in `shared-assets/`, are served at `/opennms/assets/shared/`, and are found through `manifest.json` with a small shared helper. | `packages/shared-assets/`, `plugins/`, [Part 3](docs/03-how-plugins-find-assets.md) |
| A host directory in the container deployment: drop a file in and the plugins find it | `./shared-assets` is bind-mounted read-only into the `opennms` web application. Jetty serves a new file on the next request, with no restart, rebuild or `podman exec`. | `compose.yml`, `scripts/assets.py`, [Part 7](docs/07-working-with-the-shared-folder.md) |
| A teaching guide: where assets are stored, how plugins find them, how Jetty serves them | Ten parts plus a source trace with a link to every file and line the explanations rely on. | [docs/](docs/README.md) |
| The architecture of OpenNMS: process and JVM, Karaf, Felix, Jetty, bundles and plugins, deployment, how one server serves many plugin UIs | 16 steps, each with a diagram and commands to see it in the running lab | [docs/architecture/](docs/architecture/README.md) |

## Quick start

```bash
cp .env.example .env && chmod 600 .env && vi .env    # choose the two database passwords
podman-compose pull                                  # OpenNMS 33.1.8 + PostgreSQL 15
podman-compose run --rm horizon -i                   # create the database and configuration
podman-compose up -d
scripts/wait-for-opennms.sh                          # returns when the web UI is ready
```

Log in at <http://localhost:8980/opennms> as `admin` / `admin`, change the password when asked,
and put the new one into `.env` (`ONMS_PASS`). Then install the plugins, one at a time:

```bash
scripts/build-plugins.sh node-inventory              # npm + Maven -> a KAR
scripts/deploy-plugin.sh node-inventory              # check it, copy it into ./deploy, wait until live
scripts/provision-demo-nodes.sh                      # some nodes for the icon rules
scripts/build-plugins.sh icon-catalog && scripts/deploy-plugin.sh icon-catalog
scripts/lab-status.sh                                # everything on one screen
```

Open <http://localhost:8980/opennms/ui/> and use the **Plugins** menu. Each command is explained
in [Part 0](docs/00-install-opennms-and-postgresql.md) and [Part 6](docs/06-installing-the-plugins.md);
[Part 7](docs/07-working-with-the-shared-folder.md) adds and changes icons while everything runs.

## How it fits together

```text
host: ./shared-assets/ ──bind mount (ro)──► /usr/share/opennms/jetty-webapps/opennms/assets/shared/
                                                    │ served by the /opennms web app's DefaultServlet
host: ./deploy/*.kar ───bind mount (ro)──► /opt/opennms-lab-deploy/ ──► Karaf installs each KAR
                                                    │                     (watcher: etc-overlay/*.cfg)
                                                    ▼
browser:  /opennms/ui/  ── Node Inventory plugin ──┐
                        ── Icon Catalog plugin  ───┴─► GET /opennms/assets/shared/icons/router.svg?rev=1
                           (each ships only its JS: /opennms/rest/plugins/ui-extension/module/<id>)
```

Why this location for the assets: under `/opennms/assets/` the files are on the UI's own origin (so
the UI's Content-Security-Policy allows them), readable without extra configuration (Spring
Security permits `/assets/**`), cached for an hour (OpenNMS's `no-store` rule exempts `assets/`),
and served by a servlet that re-checks the disk on every request. [Part 4](docs/04-how-jetty-serves-them.md)
traces a request through every layer, and [Part 5](docs/05-design-decisions.md) compares the
alternatives, for the assets and for deploying the plugins.

## Repository map

```text
compose.yml, .env.example     OpenNMS 33.1.8 + PostgreSQL 15; the three host-folder mounts are the lab
CHANGELOG.md                  what changed between versions of the lab
shared-assets/                THE shared folder: manifest.json (+ schema), icons/, branding/
deploy/                       plugin KARs: Karaf installs what you put here (empty in Git)
etc-overlay/                  copied into OpenNMS's etc/ at start: the watcher for deploy/
packages/shared-assets/       @onms-lab/shared-assets: URL building, catalog loading, node-icon rules (+ tests)
plugins/node-inventory/       demo plugin 1: node table with shared icons (Java + blueprint + Vite + KAR)
plugins/icon-catalog/         demo plugin 2: the catalog, with the HTTP headers Jetty sends, and a probe box
scripts/lib.sh                shared by the shell scripts: reads .env, login check, REST helpers
scripts/wait-for-opennms.sh   waits for the health probe and shows what a starting OpenNMS waits for
scripts/lab-status.sh         containers, health, version, shared folder, KARs and registered plugins
scripts/build-plugins.sh      npm + contract check + Maven, one plugin or all
scripts/deploy-plugin.sh      check a KAR, copy it into deploy/ safely, wait until OpenNMS serves it
scripts/undeploy-plugin.sh    remove a KAR from deploy/, wait until OpenNMS drops the plugin
scripts/karaf.sh              one Karaf shell command (kar:list, feature:list, ...) or the shell
scripts/kar_info.py           what is inside a KAR: name, Karaf-Feature-Start, features, bundles, UI extensions
scripts/check_plugins.py      checks a plugin (source tree or KAR) against the rules of the 33.1.8 plugin loader
scripts/assets.py             add / validate / list / bump for the shared folder (atomic, permission-safe)
scripts/verify-assets.sh      receiver-side HTTP checks against a running OpenNMS
scripts/provision-demo-nodes.sh  demo requisition that exercises every icon rule
scripts/check_links.py        checks every relative link and heading anchor in the Markdown files
scripts/validate-repo.sh      offline sweep: JSON, XML, compose, scripts, folder, plugin contract, diagrams, links, tests, lint
tests/scripts/                unit tests for kar_info, check_plugins on KARs, and lib.sh
tests/e2e/                    Playwright test: both plugins render the same files, one manifest fetch, no CSP errors
docs/                         the teaching guide (start at docs/README.md)
docs/architecture/            the architecture guide: 16 steps, diagrams generated by images/make_diagrams.py
```

## What was verified

The source of OpenNMS 33.1.8, the Horizon container image, OIA 1.6.1, Jetty 9.4.57, Karaf 4.3.10,
Felix FileInstall 3.7.4 and the Felix framework 6.0.5 was read for every claim
([source trace](docs/reference/source-trace.md)).
Serving behaviour, the plugin loader and both demo plugins were exercised in a test harness built
from OpenNMS's own `jetty.xml` and `web.xml`, with Chromium. `compose.yml` and the by-hand commands
of Part 0 were run with Podman 4.9.3 and podman-compose 1.6.0 using stand-in images, and the deploy
scripts against a stand-in for the Karaf deploy folder and the plugin REST API. The real OpenNMS
container and the Maven build could not be run where this was written;
[verification](docs/reference/verification.md) lists exactly what was and was not tested, and
`scripts/lab-status.sh`, `scripts/verify-assets.sh` and `tests/e2e` close the gap on your machine.

## Requirements

Podman 4+ with podman-compose 1.3+ (or Docker with Compose v2), Python 3, curl. For building the
plugins: Node.js 18.18+ with npm, JDK 11 or 17 and Maven 3.8+. About 4 GB of memory for the
containers. Details per operating system are in [Part 0](docs/00-install-opennms-and-postgresql.md#02-prerequisites).
