# Reference: what was verified, and how

This guide was written without access to a running OpenNMS container: the build environment
could not pull images from Docker Hub or artifacts from Maven Central. Everything that could be
checked without them was checked against the real code; this page says what, how, and what is
left for you to confirm in the lab.

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

## Browser behaviour (Chromium through Playwright, against the harness)

| # | Check | Result |
|---|---|---|
| 1 | Node Inventory: every shared image decoded (`naturalWidth > 0`) | pass, 9 images |
| 2 | Node Inventory: image URLs are `/opennms/assets/shared/...?rev=N` | pass |
| 3 | Node Inventory: rule results (router, switch, firewall, wifi-ap, sbc, linux, server, unknown) | pass |
| 4 | Icon Catalog: every catalog image decoded | pass, 9 images |
| 5 | Icon Catalog: `HEAD` shows `Cache-Control: max-age=3600,public` | pass |
| 6 | both plugins in one page session caused one `manifest.json` request | pass (1 request) |
| 7 | a file written on the host while the page is open is served and rendered (Probe box) | pass |
| 8 | images packed in a bundle, requested through `/rest/plugins/ui-extension/module/...` | fail to render, as expected (SVG and PNG) |
| 9 | an image from another origin (`127.0.0.1` vs `localhost`) | blocked by CSP `img-src` |
| 10 | revision bump in `manifest.json` then reload | every URL carries the new `?rev=` |
| 11 | CSP violations caused by the plugins | none |

The shipped Playwright test (`tests/e2e/shared-assets.spec.ts`) was also run against the harness,
with the login step skipped: 2 of 2 tests passed.

## Build and static checks

| Check | Result |
|---|---|
| `@onms-lab/shared-assets` unit tests (Vitest 2.1.9) | 31 of 31 passed |
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
| JSON Schema validation of `manifest.json`, `shellcheck` on the shell scripts, `tsc` on the Playwright spec, `markdownlint`, internal link check of all docs, rendering of every Mermaid diagram | clean |
| Vite library mode with a 49 KB PNG import | inlined as a `data:` URI (confirms Part 1) |
| Vite library mode with `url(/opennms/assets/shared/...)` in CSS | kept unchanged, with the "will remain unchanged to be resolved at runtime" notice |

## Not verified here: please confirm in your lab

1. **The real container.** Run `scripts/verify-assets.sh --live-drop --plugins` and the Playwright
   test in `tests/e2e` against the compose lab. They check the same things as the harness, on the
   real stack.
2. **Spring Security.** The anonymous access to `/assets/**` and the roles for `/rest/**` come from
   reading `applicationContext-spring-security.xml`. `verify-assets.sh` checks the anonymous part
   (it sends no credentials for the shared files).
3. **The Maven/KAR build.** The POMs follow the OIA 1.6.1 `example-kar-plugin` archetype and the
   KAR module of the VeloCloud plugin (built by OpenNMS's CI), but they were not run here.
   `scripts/build-plugins.sh` runs them.
4. **The OSGi path.** Blueprint, `UIExtensionRegistryImpl`, the JAX-RS connector and the
   `ProxyFilter` were traced in the source and emulated in the harness, not executed. The Karaf
   commands in Part 6 show each layer in the real system.
5. **Podman specifics.** The `z` relabel option and rootless user mapping follow Podman's
   documented behaviour and were not exercised on an SELinux host.
