# Part 6 - Lab walkthrough

Hands-on: start OpenNMS with the shared folder, prove the folder is served, deploy the two demo
plugins, give them some nodes, then add and change an icon while everything runs.

## 6.0 Prerequisites

| Tool | Used for | Notes |
|---|---|---|
| Podman 4+ with `podman-compose` (or Docker with `docker compose`) | running OpenNMS and PostgreSQL | commands below use Podman; replace `podman` with `docker` if needed |
| Node.js 18.18+ and npm | building the helper and the Vue modules | the built modules are committed, so this is optional unless you change the UI code |
| JDK 11+ and Maven 3.8+ | building the bundles and KARs | needs access to Maven Central |
| Python 3 and curl | the scripts in `scripts/` | standard library only |

Give the container runtime at least 4 GB of memory. The first start initialises the database and
takes a few minutes.

## 6.1 Start OpenNMS with the shared folder

```bash
cp .env.example .env          # optional; the defaults work
podman-compose up -d
podman logs -f onms-shared-assets-horizon    # wait for the web UI; Ctrl-C to stop following
```

OpenNMS is ready when its health probe answers: `podman healthcheck run onms-shared-assets-horizon`
exits with 0 (and `podman ps` shows `healthy` where Podman runs health checks automatically). Log in at <http://localhost:8980/opennms> as `admin` / `admin` and change the password
if the machine is reachable by others.

## 6.2 Prove the folder is served

```bash
scripts/verify-assets.sh
```

Every entry of `manifest.json` should come back `200` with the right `Content-Type` and
`Cache-Control: max-age=3600,public`, the directory request should be refused, and the favicon
check shows the `no-store` policy that applies outside `/opennms/assets/`. Example output (from the
test harness):

```text
== Shared folder served by Jetty at http://localhost:8980/opennms/assets/shared/
PASS  manifest.json -> 200 without login (application/json)
PASS  icons/router.svg -> 200 image/svg+xml, Cache-Control: max-age=3600,public
...
PASS  branding/lab-banner.png -> 200 image/png, Cache-Control: max-age=3600,public
PASS  directory listing disabled (icons/ -> 403): plugins must use manifest.json to discover files
PASS  contrast: /opennms/favicon.ico (outside /assets/) -> Cache-Control: no-store (jetty.xml RewriteHandler rule)
```

Now the live test: the script writes a file into `./shared-assets` on the host, fetches it through
OpenNMS straight away, deletes it and checks for the `404`.

```bash
scripts/verify-assets.sh --live-drop
```

You can look at the mount from inside the container too; note that the file listing matches the
host folder exactly, because it *is* the host folder:

```bash
podman exec onms-shared-assets-horizon ls -l /usr/share/opennms/jetty-webapps/opennms/assets/shared/icons
```

## 6.3 Build and deploy the two plugins

```bash
scripts/build-plugins.sh
```

The script runs the helper's unit tests, builds both Vue modules, checks them with
`scripts/check_plugins.py`, runs `mvn package` for both plugins, and copies the two KARs into
`overlay/deploy/`. The entrypoint copies that folder into `$OPENNMS_HOME/deploy/` at start, so:

```bash
podman-compose restart horizon
```

(Or, without a restart: `podman cp overlay/deploy/<kar> onms-shared-assets-horizon:/usr/share/opennms/deploy/`
for each KAR. Karaf watches `deploy/` and installs a new KAR within seconds.)

Check each layer from Part 3 in turn. In the Karaf shell (`ssh -p 8101 admin@localhost`,
password `admin`):

```text
admin@opennms()> kar:list
admin@opennms()> feature:list | grep opennms-lab
admin@opennms()> bundle:list | grep -i "Shared Assets"
admin@opennms()> service:list org.opennms.integration.api.v1.ui.UIExtension
```

Then the REST layer, and the module and CSS endpoints:

```bash
curl -s -u admin:admin http://localhost:8980/opennms/rest/plugins | python3 -m json.tool
scripts/verify-assets.sh --plugins
```

## 6.4 Give the plugins something to show

```bash
scripts/provision-demo-nodes.sh
```

This creates a requisition `SharedAssetsLab` with seven nodes whose categories and labels
exercise the rules in `manifest.json` (router, switch, firewall, access point, a Raspberry Pi by
name, a server, and one that matches nothing). The addresses are documentation addresses
(`192.0.2.0/24`) and the foreign-source definition has no detectors, so nothing is scanned. The
`linux` rule matches on sysObjectID, which only real SNMP nodes have; add your Raspberry Pi running
net-snmp and label it without "pi" to see it.

## 6.5 Open the plugins

Open <http://localhost:8980/opennms/ui/> and use the **Plugins** menu, or go directly to:

* <http://localhost:8980/opennms/ui/#/plugins/labNodeInventory/node-inventory/nodeInventory.es.js>
* <http://localhost:8980/opennms/ui/#/plugins/labIconCatalog/icon-catalog/iconCatalog.es.js>

In the browser's developer tools (Network tab) you should see the plugin modules come from
`/opennms/rest/plugins/ui-extension/module/...` and every image from
`/opennms/assets/shared/...?rev=1`, and `manifest.json` requested once even after switching
between the two plugins. The Icon Catalog shows the `Content-Type` and `Cache-Control` Jetty sent
for each file.

![Node Inventory rendered in the test harness](images/harness-node-inventory.png)

*The Node Inventory plugin rendered by the lab's test harness, which emulates the OpenNMS plugin
host. In OpenNMS the same component appears inside the normal UI frame.*

## 6.6 Add an icon while everything runs

Create an icon (here: a recoloured copy of the router icon) and register it with a rule for a new
category:

```bash
sed 's/#1f6feb/#b45309/; s/>Router</>Load balancer</' shared-assets/icons/router.svg > /tmp/lb.svg
python3 scripts/assets.py add /tmp/lb.svg --key load-balancer --label "Load balancer" --category LoadBalancers
```

Give a node that category:

```bash
curl -s -u admin:admin -H 'Content-Type: application/xml' -X POST \
  http://localhost:8980/opennms/rest/requisitions/SharedAssetsLab/nodes --data-binary \
  '<node xmlns="http://xmlns.opennms.org/xsd/config/model-import" foreign-id="lb-01" node-label="lb-01"><interface ip-addr="192.0.2.8" status="1" snmp-primary="N"/><category name="LoadBalancers"/></node>'
curl -s -u admin:admin -X PUT 'http://localhost:8980/opennms/rest/requisitions/SharedAssetsLab/import?rescanExisting=false'
```

Reload either plugin page. Both show the new icon, the Icon Catalog lists it, and every image URL
now ends in `?rev=2`. Nothing was rebuilt, redeployed or restarted.

The Icon Catalog's **Probe a path** box demonstrates the plain-URL case: copy any image into
`shared-assets/icons/`, type `icons/<file name>` and press **Check**; Jetty serves it on the spot,
before any manifest edit.

![Icon Catalog rendered in the test harness](images/harness-icon-catalog.png)

*The Icon Catalog in the test harness: each card shows the `Content-Type` and `Cache-Control` Jetty
returned for that file.*

## 6.7 Change an existing icon

Edit or replace `shared-assets/icons/server.svg`, then:

```bash
python3 scripts/assets.py bump
```

Reload: the new revision makes every URL new, so no browser keeps the old picture. Skip the bump
and a browser that loaded the page in the last hour may keep showing the old one, exactly as
described in Part 4.

## 6.8 Browser test

`tests/e2e` holds a Playwright test that logs in, opens both plugins in one page session, and
checks that every shared image decoded, that both plugins used the same files, that
`manifest.json` was fetched once, and that the CSP reported nothing.

```bash
cd tests/e2e
npm install
npm run install-browser
npm test          # ONMS_URL, ONMS_USER, ONMS_PASS override the defaults
```

## 6.9 Clean up

```bash
podman-compose down        # keeps the database and config volumes
podman-compose down -v     # removes them too
```
