# Reference: source trace

Every statement about OpenNMS, the Integration API, Jetty and Karaf in this guide rests on the lines
below. Links point at the exact tags: OpenNMS `opennms-33.1.8-1`, OIA `v1.6.1`, Jetty
`jetty-9.4.57.v20241219` (the version pinned by OpenNMS 33.1.8), Karaf `karaf-4.3.10`, Felix
FileInstall `org.apache.felix.fileinstall-3.7.4` and the Felix framework
`org.apache.felix.framework-6.0.5` (the versions Karaf 4.3.10 ships). Line numbers were computed
from those tags when this guide was written. The last three sections back the
[architecture guide](../architecture/README.md).

## OpenNMS 33.1.8: UI extensions

| What | Where |
|---|---|
| REST resource root `/plugins` | [`UIExtensionService.java:37`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/ui-extension/src/main/java/org/opennms/features/uiextension/api/UIExtensionService.java#L37) |
| module endpoint always answers `application/javascript` | [`UIExtensionService.java:45`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/ui-extension/src/main/java/org/opennms/features/uiextension/api/UIExtensionService.java#L45) |
| CSS endpoint always answers `text/css` | [`UIExtensionService.java:50`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/ui-extension/src/main/java/org/opennms/features/uiextension/api/UIExtensionService.java#L50) |
| CSS path is fixed: `<resourceRootPath>/style.css` | [`UIExtensionServiceImpl.java:57`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/ui-extension/src/main/java/org/opennms/features/uiextension/impl/UIExtensionServiceImpl.java#L57) |
| the bundle is found through `getExtensionClass()` | [`UIExtensionServiceImpl.java:62`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/ui-extension/src/main/java/org/opennms/features/uiextension/impl/UIExtensionServiceImpl.java#L62) |
| file content becomes a `String` (JVM default charset) | [`UIExtensionServiceImpl.java:70`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/ui-extension/src/main/java/org/opennms/features/uiextension/impl/UIExtensionServiceImpl.java#L70) |
| published through the OSGi JAX-RS connector under `/rest` | [`blueprint.xml:13`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/ui-extension/src/main/resources/OSGI-INF/blueprint/blueprint.xml#L13) |
| API layer tracks every `UIExtension` service | [`blueprint.xml:431`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/api-layer/core/src/main/resources/OSGI-INF/blueprint/blueprint.xml#L431) |
| registry keyed by `extensionId` (last one wins) | [`UIExtensionRegistryImpl.java:41`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/api-layer/core/src/main/java/org/opennms/features/apilayer/uiextension/UIExtensionRegistryImpl.java#L41) |

## OpenNMS 33.1.8: web bridge and Karaf inside the webapp

| What | Where |
|---|---|
| `ProxyFilter` web.xml fragment (merged into the opennms webapp) | [`web.xml:40`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/servlet/src/main/webapp/WEB-INF/web.xml#L40) |
| REST endpoints are always forwarded to OSGi | [`ProxyFilter.java:90`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/bridge/proxy/src/main/java/org/opennms/container/web/bridge/proxy/ProxyFilter.java#L90) |
| dispatch into the Felix HTTP bridge | [`ProxyFilter.java:101`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/bridge/proxy/src/main/java/org/opennms/container/web/bridge/proxy/ProxyFilter.java#L101) |
| whiteboard resources are supported too | [`ResourceTracker.java:45`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/bridge/proxy/src/main/java/org/opennms/container/web/bridge/proxy/trackers/ResourceTracker.java#L45) |
| the JAX-RS connector (`com.eclipsesource.jaxrs` publisher) | [`pom.xml:35`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/bridge/rest/pom.xml#L35) |
| Karaf is started by the webapp; `karaf.data` = `OPENNMS_HOME/data` | [`WebAppListener.java:66`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/servlet/src/main/java/org/opennms/container/web/WebAppListener.java#L66) |
| merge point for extra filter mappings (after Spring Security) | [`web.xml:420`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/web.xml#L420) |
| core REST v1 is a CXF servlet on `/rest/*` (v2 on `/api/v2/*`) | [`web.xml:87`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp-rest/src/main/webapp/WEB-INF/web.xml#L87) |

## OpenNMS 33.1.8: the new UI (plugin host)

| What | Where |
|---|---|
| Vue, Pinia, VueRouter published on `window` for plugins | [`main.ts:96`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/src/main.ts#L96) |
| plugins listed before the app mounts | [`main.ts:103`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/src/main.ts#L103) |
| route per plugin (one segment per parameter) | [`main.ts:115`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/src/main.ts#L115) |
| extension id parsed from the module URL | [`utils.ts:40`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/src/components/Plugin/utils.ts#L40) |
| module file name must contain `.es` | [`utils.ts:48`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/src/components/Plugin/utils.ts#L48) |
| module loaded with `<script type="module" crossorigin="use-credentials">` | [`utils.ts:65`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/src/components/Plugin/utils.ts#L65) |
| module URL format | [`utils.ts:98`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/src/components/Plugin/utils.ts#L98) |
| Plugins menu link format | [`Menubar.vue:410`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/src/components/Layout/Menubar.vue#L410) |
| the UI hard-codes `/opennms/rest` at build time | [`.env:2`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/.env#L2) |
| router base `/opennms/ui` | [`index.ts:59`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/src/router/index.ts#L59) |
| host Vue runtime resolves to 3.3.7 | [`yarn.lock:4587`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/ui/yarn.lock#L4587) |
| the UI is unpacked into the webapp as `ui/` | [`pom.xml:56`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/pom.xml#L56) |

## OpenNMS 33.1.8: Jetty configuration

| What | Where |
|---|---|
| `etc/jetty.xml` wins if it exists | [`JettyServer.java:66`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/java/org/opennms/netmgt/jetty/JettyServer.java#L66) |
| otherwise the built-in file | [`JettyServer.java:86`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/java/org/opennms/netmgt/jetty/JettyServer.java#L86) |
| built-in file shipped as `etc/examples/jetty.xml` | [`etc.xml:14`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/assembly/etc.xml#L14) |
| `X-Frame-Options: SAMEORIGIN` on every response | [`jetty.xml:128`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/resources/org/opennms/netmgt/jetty/jetty.xml#L128) |
| `no-store` / `no-cache` for everything under `/opennms/` except `assets/` | [`jetty.xml:135`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/resources/org/opennms/netmgt/jetty/jetty.xml#L135) |
| contexts chosen by path | [`jetty.xml:170`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/resources/org/opennms/netmgt/jetty/jetty.xml#L170) |
| `jetty-webapps/` scanned every 10 s | [`jetty.xml:212`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/resources/org/opennms/netmgt/jetty/jetty.xml#L212) |
| extra alias check for double slashes | [`OpenNMSWebAppProvider.java:49`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/java/org/opennms/netmgt/jetty/OpenNMSWebAppProvider.java#L49) |

## OpenNMS 33.1.8: the opennms web application

| What | Where |
|---|---|
| CSP: images only from `self`, `data:` and three tile hosts | [`web.xml:112`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/web.xml#L112) |
| `X-Content-Type-Options: nosniff` | [`web.xml:128`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/web.xml#L128) |
| OpenNMS overrides the `default` servlet | [`web.xml:535`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/web.xml#L535) |
| `dirAllowed=false` | [`web.xml:547`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/web.xml#L547) |
| `cacheControl=max-age=3600,public` | [`web.xml:583`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/web.xml#L583) |
| `/assets/**` readable anonymously | [`applicationContext-spring-security.xml:307`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/applicationContext-spring-security.xml#L307) |
| everything else needs `ROLE_USER` | [`applicationContext-spring-security.xml:333`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/applicationContext-spring-security.xml#L333) |
| `GET /rest/**` roles | [`applicationContext-spring-security.xml:108`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/applicationContext-spring-security.xml#L108) |

## OpenNMS 33.1.8: container image

| What | Where |
|---|---|
| `/opt/opennms` is a symlink to `/usr/share/opennms` | [`Dockerfile:114`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L114) |
| user `opennms` created with uid 10001 and its own group 10001 | [`Dockerfile:67`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L67) |
| runs as uid 10001 | [`Dockerfile:155`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L155) |
| ports: web 8980, Karaf SSH 8101 | [`Dockerfile:182`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L182) |
| declared volumes | [`Dockerfile:169`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L169) |
| plugin KARs pre-installed in `deploy/` | [`Dockerfile:81`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L81) |
| entrypoint flags `-f`, `-i`, `-s`, `-t` | [`entrypoint.sh:73`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L73) |
| `etc/configured` skips the installer | [`entrypoint.sh:80`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L80) |
| empty `etc/` initialised from `etc-pristine` | [`entrypoint.sh:117`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L117) |
| overlay copied at start (not live, never deletes) | [`entrypoint.sh:147`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L147) |
| etc overlay copied into `etc/` at every start | [`entrypoint.sh:155`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L155) |
| `-s` runs the configuration tester, then the installer, then starts | [`entrypoint.sh:221`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L221) |
| the image's `/health.sh` passes `-sSF` to curl | [`health.sh:3`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/health.sh#L3) |
| in the container, Karaf SSH listens on all interfaces | [`org.apache.karaf.shell.cfg.tmpl:6`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/confd/templates/org.apache.karaf.shell.cfg.tmpl#L6) |
| `opennms.home` = `/usr/share/opennms` | [`entrypoint.sh:173`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L173) |
| database settings come from environment variables | [`opennms-datasources.xml.tmpl:20`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/confd/templates/opennms-datasources.xml.tmpl#L20) |
| Jetty 9.4.57.v20241219 | [`pom.xml:1847`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/pom.xml#L1847) |
| Integration API 1.6.1 | [`pom.xml:1927`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/pom.xml#L1927) |
| Karaf 4.3.10 | [`pom.xml:1879`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/pom.xml#L1879) |

## OpenNMS 33.1.8: installation, health checks, logins

| What | Where |
|---|---|
| the installer writes `etc/configured` | [`Installer.java:357`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-install/src/main/java/org/opennms/install/Installer.java#L357) |
| the `opennms` database user is only created if missing (its password is never changed) | [`Migrator.java:437`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/schema/src/main/java/org/opennms/core/schema/Migrator.java#L437) |
| health probe answer when every check is green | [`HealthCheckRestServiceImpl.java:47`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/health/rest/src/main/java/org/opennms/core/health/rest/internal/HealthCheckRestServiceImpl.java#L47) |
| otherwise HTTP 599 | [`UnhealthyStatusType.java:29`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/health/rest/src/main/java/org/opennms/core/health/rest/internal/UnhealthyStatusType.java#L29) |
| the probe needs no login | [`applicationContext-spring-security.xml:49`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/applicationContext-spring-security.xml#L49) |
| `/rest/info` (version) | [`InfoRestService.java:56`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp-rest/src/main/java/org/opennms/web/rest/v1/InfoRestService.java#L56) |
| every `admin`/`admin` login is sent to the password gate | [`OpenNMSAuthSuccessHandler.java:57`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/springframework-security/src/main/java/org/opennms/web/springframework/security/OpenNMSAuthSuccessHandler.java#L57) |
| Karaf's login realm replaced by OpenNMS users | [`blueprint.xml:14`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/jaas-login-module/src/main/resources/OSGI-INF/blueprint/blueprint.xml#L14) |
| ... admins only | [`OpenNMSLoginModule.java:117`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/jaas-login-module/src/main/java/org/opennms/container/jaas/OpenNMSLoginModule.java#L117) |
| default discovery pings 127.0.0.1 into requisition `selfmonitor` | [`discovery-configuration.xml:9`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-base-assembly/src/main/filtered/etc/discovery-configuration.xml#L9) |
| `etc/featuresBoot.d/` read at start | [`KarafExtender.java:81`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/extender/src/main/java/org/opennms/karaf/extender/KarafExtender.java#L81) |
| `wait-for-kar=<KAR name>` | [`KarafExtender.java:73`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/extender/src/main/java/org/opennms/karaf/extender/KarafExtender.java#L73) |
| waits until the KAR is installed (no time limit)... | [`KarDependencyHandler.java:74`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/extender/src/main/java/org/opennms/karaf/extender/KarDependencyHandler.java#L74) |
| ...reporting "Starting" to the health check meanwhile | [`KarafExtender.java:448`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/extender/src/main/java/org/opennms/karaf/extender/KarafExtender.java#L448) |

## OpenNMS 33.1.8: documentation used by Part 0

| What | Where |
|---|---|
| PostgreSQL 10.x to 15.x compatible | [`antora.yml:25`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/docs/antora.yml#L25) |
| the docs use PostgreSQL 15 | [`antora.yml:29`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/docs/antora.yml#L29) |
| "just testing": 4 GB RAM (2 cores, 50 GB disk) | [`system-requirements.adoc:16`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/docs/modules/deployment/pages/core/system-requirements.adoc#L16) |
| `max_connections` at least 100 | [`getting-started.adoc:79`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/docs/modules/deployment/pages/core/getting-started.adoc#L79) |
| initialise with `-i`, then start | [`initialize.adoc:11`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/docs/modules/deployment/pages/core/docker/initialize.adoc#L11) |
| upgrades: delete `etc/configured` | [`initialize.adoc:21`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/docs/modules/deployment/pages/core/docker/initialize.adoc#L21) |
| the `ping_group_range` sysctl for uid/gid 10001 | [`minion.adoc:68`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/docs/modules/deployment/pages/minion/docker/minion.adoc#L68) |

## Integration API 1.6.1

| What | Where |
|---|---|
| "root path of UI extension web assets inside the bundle" | [`UIExtension.java:51`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/api/src/main/java/org/opennms/integration/api/v1/ui/UIExtension.java#L51) |
| "used to lookup OSGI bundle" | [`UIExtension.java:61`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/api/src/main/java/org/opennms/integration/api/v1/ui/UIExtension.java#L61) |
| scaffold externalises Vue, Pinia, vue-router | [`vite.config.ts:10`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/ui-extension/vite.config.ts#L10) |
| the scaffold imports an image... | [`App.vue:4`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/ui-extension/src/App.vue#L4) |
| ...which the build inlines as base64 | [`uiextension.es.js:1`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/sample/src/main/resources/ui-ext/uiextension.es.js#L1) |
| the archetype KAR does not auto-install its feature | [`pom.xml:32`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/archetypes/example-kar-plugin/src/main/resources/archetype-resources/assembly/kar/pom.xml#L32) |
| the VeloCloud plugin (shipped in the image) does the same (repository head, `2f3ed08`) | [`pom.xml:31`](https://github.com/OpenNMS/opennms-velocloud-plugin/blob/2f3ed0818793245e2657e032efb2d9aa5d236cb7/assembly/kar/pom.xml#L31) |
| ...and puts the version into the KAR file name | [`pom.xml:27`](https://github.com/OpenNMS/opennms-velocloud-plugin/blob/2f3ed0818793245e2657e032efb2d9aa5d236cb7/assembly/kar/pom.xml#L27) |

## Jetty 9.4.57

| What | Where |
|---|---|
| `Cache-Control` only added when absent | [`ResourceService.java:845`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-server/src/main/java/org/eclipse/jetty/server/ResourceService.java#L845) |
| cache entries validated by modification time and length | [`CachedContentFactory.java:475`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-server/src/main/java/org/eclipse/jetty/server/CachedContentFactory.java#L475) |
| missing files are not cached | [`CachedContentFactory.java:221`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-server/src/main/java/org/eclipse/jetty/server/CachedContentFactory.java#L221) |
| symlinks allowed by default on Unix | [`ContextHandler.java:275`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-server/src/main/java/org/eclipse/jetty/server/handler/ContextHandler.java#L275) |
| header rules set headers only | [`HeaderRegexRule.java:89`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-rewrite/src/main/java/org/eclipse/jetty/rewrite/handler/HeaderRegexRule.java#L89) |
| `gzip=true` serves precompressed `.gz` files | [`DefaultServlet.java:179`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-servlet/src/main/java/org/eclipse/jetty/servlet/DefaultServlet.java#L179) |
| only direct children of `jetty-webapps/` are watched | [`ScanningAppProvider.java:144`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-deploy/src/main/java/org/eclipse/jetty/deploy/providers/ScanningAppProvider.java#L144) |
| MIME types | [`mime.properties:152`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-http/src/main/resources/org/eclipse/jetty/http/mime.properties#L152) |
| stock `webdefault.xml`: `dirAllowed` true | [`webdefault.xml:151`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-webapp/src/main/config/etc/webdefault.xml#L151) |

## Karaf 4.3.10

| What | Where |
|---|---|
| KARs extracted to `${karaf.data}/kar` | [`Activator.java:47`](https://github.com/apache/karaf/blob/karaf-4.3.10/kar/src/main/java/org/apache/karaf/kar/internal/osgi/Activator.java#L47) |
| `Karaf-Feature-Start: false` disables auto-install | [`Kar.java:104`](https://github.com/apache/karaf/blob/karaf-4.3.10/kar/src/main/java/org/apache/karaf/kar/internal/Kar.java#L104) |
| otherwise the KAR installs its features | [`KarServiceImpl.java:124`](https://github.com/apache/karaf/blob/karaf-4.3.10/kar/src/main/java/org/apache/karaf/kar/internal/KarServiceImpl.java#L124) |
| only features with install mode `auto` are installed | [`KarServiceImpl.java:304`](https://github.com/apache/karaf/blob/karaf-4.3.10/kar/src/main/java/org/apache/karaf/kar/internal/KarServiceImpl.java#L304) |
| a failed feature is only a warning | [`KarServiceImpl.java:317`](https://github.com/apache/karaf/blob/karaf-4.3.10/kar/src/main/java/org/apache/karaf/kar/internal/KarServiceImpl.java#L317) |
| uninstalling a KAR uninstalls its features | [`KarServiceImpl.java:256`](https://github.com/apache/karaf/blob/karaf-4.3.10/kar/src/main/java/org/apache/karaf/kar/internal/KarServiceImpl.java#L256) |
| a KAR name already installed is skipped | [`KarArtifactInstaller.java:43`](https://github.com/apache/karaf/blob/karaf-4.3.10/deployer/kar/src/main/java/org/apache/karaf/deployer/kar/KarArtifactInstaller.java#L43) |
| log: `Installing KAR file ...` | [`KarArtifactInstaller.java:48`](https://github.com/apache/karaf/blob/karaf-4.3.10/deployer/kar/src/main/java/org/apache/karaf/deployer/kar/KarArtifactInstaller.java#L48) |
| a changed file = uninstall + install | [`KarArtifactInstaller.java:60`](https://github.com/apache/karaf/blob/karaf-4.3.10/deployer/kar/src/main/java/org/apache/karaf/deployer/kar/KarArtifactInstaller.java#L60) |
| a deleted file = uninstall | [`KarArtifactInstaller.java:55`](https://github.com/apache/karaf/blob/karaf-4.3.10/deployer/kar/src/main/java/org/apache/karaf/deployer/kar/KarArtifactInstaller.java#L55) |
| KAR name = file name without extension | [`KarArtifactInstaller.java:67`](https://github.com/apache/karaf/blob/karaf-4.3.10/deployer/kar/src/main/java/org/apache/karaf/deployer/kar/KarArtifactInstaller.java#L67) |
| Karaf's own `deploy/` is a FileInstall factory configuration | [`org.apache.felix.fileinstall-deploy.cfg:20`](https://github.com/apache/karaf/blob/karaf-4.3.10/assemblies/features/framework/src/main/resources/resources/etc/org.apache.felix.fileinstall-deploy.cfg#L20) |
| its settings, copied by the lab's `.cfg` | [`org.apache.felix.fileinstall-deploy.cfg:23`](https://github.com/apache/karaf/blob/karaf-4.3.10/assemblies/features/framework/src/main/resources/resources/etc/org.apache.felix.fileinstall-deploy.cfg#L23) |
| `etc/*.cfg` files become configurations | [`config.properties:274`](https://github.com/apache/karaf/blob/karaf-4.3.10/assemblies/features/base/src/main/filtered-resources/resources/etc/config.properties#L274) |
| log: `Adding features: ...` | [`FeaturesServiceImpl.java:815`](https://github.com/apache/karaf/blob/karaf-4.3.10/features/core/src/main/java/org/apache/karaf/features/internal/service/FeaturesServiceImpl.java#L815) |
| log: `Done.` | [`Deployer.java:1074`](https://github.com/apache/karaf/blob/karaf-4.3.10/features/core/src/main/java/org/apache/karaf/features/internal/service/Deployer.java#L1074) |
| bundle cache `${karaf.data}/cache` | [`ConfigProperties.java:298`](https://github.com/apache/karaf/blob/karaf-4.3.10/main/src/main/java/org/apache/karaf/main/ConfigProperties.java#L298) |

## Felix FileInstall 3.7.4 (used by Karaf 4.3.10)

| What | Where |
|---|---|
| factory PID `org.apache.felix.fileinstall`: each `...fileinstall-<name>.cfg` is one watcher | [`FileInstall.java:369`](https://github.com/apache/felix-dev/blob/org.apache.felix.fileinstall-3.7.4/fileinstall/src/main/java/org/apache/felix/fileinstall/internal/FileInstall.java#L369) |
| `${karaf.data}` in the `.cfg` is substituted | [`FileInstall.java:236`](https://github.com/apache/felix-dev/blob/org.apache.felix.fileinstall-3.7.4/fileinstall/src/main/java/org/apache/felix/fileinstall/internal/FileInstall.java#L236) |
| poll interval | [`DirectoryWatcher.java:173`](https://github.com/apache/felix-dev/blob/org.apache.felix.fileinstall-3.7.4/fileinstall/src/main/java/org/apache/felix/fileinstall/internal/DirectoryWatcher.java#L173) |
| the filter must match the whole file name | [`Scanner.java:89`](https://github.com/apache/felix-dev/blob/org.apache.felix.fileinstall-3.7.4/fileinstall/src/main/java/org/apache/felix/fileinstall/internal/Scanner.java#L89) |

## Architecture guide: process and daemons

| What | Where |
|---|---|
| the image runs `/entrypoint.sh` | [`Dockerfile:157`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L157) |
| the configuration tester: a short Java process through the same launcher | [`entrypoint.sh:100`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L100) |
| the installer: another short Java process | [`entrypoint.sh:87`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L87) |
| the entrypoint `exec`s Java, which becomes PID 1 | [`entrypoint.sh:186`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L186) |
| properties files read at start, in order | [`Bootstrap.java:284`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-bootstrap/src/main/java/org/opennms/bootstrap/Bootstrap.java#L284) |
| `etc/opennms.properties.d/*.properties`, sorted by name | [`Bootstrap.java:294`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-bootstrap/src/main/java/org/opennms/bootstrap/Bootstrap.java#L294) |
| a `-D` option wins over the files | [`Bootstrap.java:339`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-bootstrap/src/main/java/org/opennms/bootstrap/Bootstrap.java#L339) |
| the lib/ class loader: `lib/endorsed`, `classes`, `lib`, `etc` | [`Bootstrap.java:484`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-bootstrap/src/main/java/org/opennms/bootstrap/Bootstrap.java#L484) |
| the class to run: `Controller` unless `opennms.manager.class` says otherwise | [`Bootstrap.java:469`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-bootstrap/src/main/java/org/opennms/bootstrap/Bootstrap.java#L469) |
| ...called on a new thread named `Main` | [`Bootstrap.java:532`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-bootstrap/src/main/java/org/opennms/bootstrap/Bootstrap.java#L532) |
| `start` hands over to the `Starter` | [`Controller.java:155`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/daemon/src/main/java/org/opennms/netmgt/vmmgr/Controller.java#L155) |
| start-up logs to `manager.log` | [`Starter.java:72`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/daemon/src/main/java/org/opennms/netmgt/vmmgr/Starter.java#L72) |
| the services live in the platform MBean server | [`Starter.java:141`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/daemon/src/main/java/org/opennms/netmgt/vmmgr/Starter.java#L141) |
| a service that fails to start stops OpenNMS | [`Starter.java:161`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/daemon/src/main/java/org/opennms/netmgt/vmmgr/Starter.java#L161) |
| each service is registered as an MBean | [`Invoker.java:133`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/daemon/src/main/java/org/opennms/netmgt/vmmgr/Invoker.java#L133) |
| pass by pass, all services in file order | [`Invoker.java:226`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/daemon/src/main/java/org/opennms/netmgt/vmmgr/Invoker.java#L226) |
| log: `Invocation start successful for MBean ...` | [`Invoker.java:337`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/daemon/src/main/java/org/opennms/netmgt/vmmgr/Invoker.java#L337) |
| `TestLoadLibraries` checks ICMP and the local host name | [`Manager.java:229`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/daemon/src/main/java/org/opennms/netmgt/vmmgr/Manager.java#L229) |
| the service list (Eventd is third) | [`service-configuration.xml:22`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-base-assembly/src/main/filtered/etc/service-configuration.xml#L22) |
| `init` in pass 0, `start` in pass 1 | [`service-configuration.xml:25`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-base-assembly/src/main/filtered/etc/service-configuration.xml#L25) |
| disabled services | [`service-configuration.xml:69`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-base-assembly/src/main/filtered/etc/service-configuration.xml#L69) |
| `JettyServer`... | [`service-configuration.xml:230`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-base-assembly/src/main/filtered/etc/service-configuration.xml#L230) |
| ...followed by `KarafStartupMonitor` | [`service-configuration.xml:238`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-base-assembly/src/main/filtered/etc/service-configuration.xml#L238) |
| a daemon's `init()` loads its Spring context | [`AbstractSpringContextJmxServiceDaemon.java:98`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/daemon/src/main/java/org/opennms/netmgt/daemon/AbstractSpringContextJmxServiceDaemon.java#L98) |
| its `start()` starts the bean `daemon` | [`AbstractSpringContextJmxServiceDaemon.java:47`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/daemon/src/main/java/org/opennms/netmgt/daemon/AbstractSpringContextJmxServiceDaemon.java#L47) |
| `soaContext`: the OpenNMS service registry | [`applicationContext-soa.xml:10`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/soa/src/main/resources/META-INF/opennms/applicationContext-soa.xml#L10) |
| `daoContext` is a child of `daemonContext` | [`beanRefContext.xml:13`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-dao/src/main/resources/beanRefContext.xml#L13) |
| the connection pool lives in `daoContext`... | [`applicationContext-dao.xml:62`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-dao/src/main/resources/META-INF/opennms/applicationContext-dao.xml#L62) |
| ...and is published in the service registry | [`applicationContext-dao.xml:63`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-dao/src/main/resources/META-INF/opennms/applicationContext-dao.xml#L63) |
| `NodeDao` is published in the service registry | [`applicationContext-shared.xml:184`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-dao/src/main/resources/META-INF/opennms/applicationContext-shared.xml#L184) |
| the thresholding context... | [`beanRefContext.xml:16`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-services/src/main/resources/beanRefContext.xml#L16) |
| ...is the parent of `webContext` | [`beanRefContext.xml:16`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/resources/beanRefContext.xml#L16) |
| the web application's Spring context has `webContext` as parent | [`web.xml:59`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/web.xml#L59) |
| `KarafStartupMonitor` waits for `KarafHealthService`... | [`KarafStartupMonitor.java:65`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/karaf-health/src/main/java/org/opennms/features/karaf/health/daemon/KarafStartupMonitor.java#L65) |
| ...looking every 5 s... | [`ServiceLookupBuilder.java:43`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/soa/src/main/java/org/opennms/core/soa/lookup/ServiceLookupBuilder.java#L43) |
| ...for about 5 minutes | [`ServiceLookupBuilder.java:39`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/soa/src/main/java/org/opennms/core/soa/lookup/ServiceLookupBuilder.java#L39) |
| one log file per prefix | [`log4j2.xml:40`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-base-assembly/src/main/filtered/etc/log4j2.xml#L40) |
| start-up lines also go to the console | [`log4j2.xml:90`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-base-assembly/src/main/filtered/etc/log4j2.xml#L90) |
| configuration reloads are events | [`EventConstants.java:421`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/events/api/src/main/java/org/opennms/netmgt/events/api/EventConstants.java#L421) |

## Architecture guide: Jetty and the web application

| What | Where |
|---|---|
| `JettyServer` logs to `jetty-server.log` | [`JettyServer.java:50`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/java/org/opennms/netmgt/jetty/JettyServer.java#L50) |
| Jetty's MBeans join the platform MBean server | [`JettyServer.java:73`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/java/org/opennms/netmgt/jetty/JettyServer.java#L73) |
| `start()` starts the server | [`JettyServer.java:104`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/java/org/opennms/netmgt/jetty/JettyServer.java#L104) |
| port 8980, from `org.opennms.netmgt.jetty.port` | [`jetty.xml:27`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/resources/org/opennms/netmgt/jetty/jetty.xml#L27) |
| HTTPS (and AJP) commented out | [`jetty.xml:44`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/resources/org/opennms/netmgt/jetty/jetty.xml#L44) |
| `HandlerCollection`: rewrite, contexts, default | [`jetty.xml:162`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/resources/org/opennms/netmgt/jetty/jetty.xml#L162) |
| `MDCHandler` wraps them all... | [`jetty.xml:195`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/resources/org/opennms/netmgt/jetty/jetty.xml#L195) |
| ...with the log prefix `web` | [`MDCHandler.java:38`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/java/org/opennms/netmgt/jetty/MDCHandler.java#L38) |
| web applications come from `jetty-webapps/` | [`jetty.xml:211`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-jetty/src/main/resources/org/opennms/netmgt/jetty/jetty.xml#L211) |
| `ROOT` redirects to `/opennms/` | [`index.jsp:24`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/root-webapp/src/main/webapp/index.jsp#L24) |
| the port opens after the web applications have started | [`Server.java:394`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-server/src/main/java/org/eclipse/jetty/server/Server.java#L394) |
| `HandlerCollection` calls every handler | [`HandlerCollection.java:106`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-server/src/main/java/org/eclipse/jetty/server/handler/HandlerCollection.java#L106) |
| request threads are named `qtp<number>-<id>` | [`QueuedThreadPool.java:106`](https://github.com/jetty/jetty.project/blob/jetty-9.4.57.v20241219/jetty-util/src/main/java/org/eclipse/jetty/util/thread/QueuedThreadPool.java#L106) |
| listeners: the web UI set-up... | [`web.xml:427`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/web.xml#L427) |
| ...the Spring root context... | [`web.xml:432`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/web.xml#L432) |
| ...and, merged in, `WebAppListener` and `ProxyListener` | [`web.xml:29`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/servlet/src/main/webapp/WEB-INF/web.xml#L29) |
| the `SpaRouting` filter... | [`web.xml:257`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/WEB-INF/web.xml#L257) |
| ...answers deep links with `ui/index.html` | [`SpaRoutingFilter.java:47`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-web-api/src/main/java/org/opennms/web/servlet/SpaRoutingFilter.java#L47) |
| REST v2: CXF on `/api/v2/*` | [`web.xml:91`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp-rest/src/main/webapp/WEB-INF/web.xml#L91) |
| OpenNMS's own JARs are not copied into `WEB-INF/lib` | [`pom.xml:18`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/pom.xml#L18) |

## Architecture guide: Karaf, Felix and the bridge

| What | Where |
|---|---|
| `karaf.home` = `$OPENNMS_HOME` | [`WebAppListener.java:64`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/servlet/src/main/java/org/opennms/container/web/WebAppListener.java#L64) |
| SSH shell on, local console off, no lock | [`WebAppListener.java:72`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/servlet/src/main/java/org/opennms/container/web/WebAppListener.java#L72) |
| Karaf is launched by the web application | [`WebAppListener.java:75`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/servlet/src/main/java/org/opennms/container/web/WebAppListener.java#L75) |
| Felix's `BundleContext` goes into the servlet context | [`WebAppListener.java:81`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/servlet/src/main/java/org/opennms/container/web/WebAppListener.java#L81) |
| the registry bridge starts next to Karaf | [`WebAppListener.java:84`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/servlet/src/main/java/org/opennms/container/web/WebAppListener.java#L84) |
| Karaf's launcher JARs are in `lib/` | [`base-assembly.xml:89`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-full-assembly/src/assembly/components/base-assembly.xml#L89) |
| Karaf's launcher: a class loader for the framework JAR... | [`Main.java:519`](https://github.com/apache/karaf/blob/karaf-4.3.10/main/src/main/java/org/apache/karaf/main/Main.java#L519) |
| ...whose parent is the loader of Karaf's launcher | [`Main.java:532`](https://github.com/apache/karaf/blob/karaf-4.3.10/main/src/main/java/org/apache/karaf/main/Main.java#L532) |
| the framework starts | [`Main.java:297`](https://github.com/apache/karaf/blob/karaf-4.3.10/main/src/main/java/org/apache/karaf/main/Main.java#L297) |
| startup bundles are installed on a clean cache only | [`Main.java:303`](https://github.com/apache/karaf/blob/karaf-4.3.10/main/src/main/java/org/apache/karaf/main/Main.java#L303) |
| Karaf runs on Felix... | [`config.properties:48`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/karaf/src/main/filtered-resources/etc/config.properties#L48) |
| ...6.0.5, from `system/` | [`config.properties:54`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/karaf/src/main/filtered-resources/etc/config.properties#L54) |
| the start level rises to 100 | [`config.properties:258`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/karaf/src/main/filtered-resources/etc/config.properties#L258) |
| bundles without a start level get 80 | [`config.properties:259`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/karaf/src/main/filtered-resources/etc/config.properties#L259) |
| startup bundles and their start levels | [`startup.properties:26`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/karaf/src/main/filtered-resources/etc/startup.properties#L26) |
| 1,383 packages exported by the system bundle, 183 `org.opennms.*` | [`custom.properties:37`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/karaf/src/main/filtered-resources/etc/custom.properties#L37) |
| `bundle:list` hides start levels below 50 | [`custom.properties:25`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/karaf/src/main/filtered-resources/etc/custom.properties#L25) |
| `featuresBoot`: a stage of Karaf features, then OpenNMS's | [`org.apache.karaf.features.cfg:32`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/karaf/src/main/filtered-resources/etc/org.apache.karaf.features.cfg#L32) |
| `opennms-karaf-health` comes last | [`org.apache.karaf.features.cfg:134`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/karaf/src/main/filtered-resources/etc/org.apache.karaf.features.cfg#L134) |
| `KarafHealthService` is exported to OpenNMS | [`Activator.java:63`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/karaf-health/src/main/java/org/opennms/features/karaf/health/bundle/Activator.java#L63) |
| the Felix HTTP bridge bundle | [`features.xml:1850`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/features/src/main/resources/features.xml#L1850) |
| the JAX-RS connector feature | [`features.xml:1207`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/features/src/main/resources/features.xml#L1207) |
| thread `FelixStartLevel` (Felix framework 6.0.5) | [`FrameworkStartLevelImpl.java:35`](https://github.com/apache/felix-dev/blob/org.apache.felix.framework-6.0.5/framework/src/main/java/org/apache/felix/framework/FrameworkStartLevelImpl.java#L35) |
| thread `FelixDispatchQueue` | [`EventDispatcher.java:117`](https://github.com/apache/felix-dev/blob/org.apache.felix.framework-6.0.5/framework/src/main/java/org/apache/felix/framework/EventDispatcher.java#L117) |
| thread `fileinstall-<folder>` | [`DirectoryWatcher.java:168`](https://github.com/apache/felix-dev/blob/org.apache.felix.fileinstall-3.7.4/fileinstall/src/main/java/org/apache/felix/fileinstall/internal/DirectoryWatcher.java#L168) |
| every OpenNMS registration... | [`OnmsOSGiBridgeActivator.java:74`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/soa/src/main/java/org/opennms/core/soa/support/OnmsOSGiBridgeActivator.java#L74) |
| ...is registered in OSGi with `registration.source=onms` | [`OnmsOSGiBridgeActivator.java:114`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/soa/src/main/java/org/opennms/core/soa/support/OnmsOSGiBridgeActivator.java#L114) |
| OSGi services with `registration.export`... | [`OnmsOSGiBridgeActivator.java:77`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/soa/src/main/java/org/opennms/core/soa/support/OnmsOSGiBridgeActivator.java#L77) |
| ...are registered in OpenNMS with `registration.source=osgi` | [`OnmsOSGiBridgeActivator.java:190`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/core/soa/src/main/java/org/opennms/core/soa/support/OnmsOSGiBridgeActivator.java#L190) |
| the api-layer references the internal `NodeDao`... | [`blueprint.xml:28`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/api-layer/core/src/main/resources/OSGI-INF/blueprint/blueprint.xml#L28) |
| ...and registers the Integration API `NodeDao` | [`blueprint.xml:54`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/api-layer/core/src/main/resources/OSGI-INF/blueprint/blueprint.xml#L54) |
| a whiteboard servlet pattern | [`blueprint.xml:45`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/vaadin-dashboard/src/main/resources/OSGI-INF/blueprint/blueprint.xml#L45) |
| the wallboard's `PageNavEntry` is exported | [`blueprint.xml:54`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/vaadin-dashboard/src/main/resources/OSGI-INF/blueprint/blueprint.xml#L54) |
| the admin page lists `(Page=admin)` entries | [`index.jsp:384`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-webapp/src/main/webapp/admin/index.jsp#L384) |
| Vaadin applications become servlet services | [`ApplicationFactoryServiceTracker.java:113`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/features/vaadin-components/extender-service/src/main/java/org/opennms/vaadin/extender/internal/extender/ApplicationFactoryServiceTracker.java#L113) |
| the `ProxyFilter` tracks the bridge's dispatcher... | [`DispatcherTracker.java:52`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/bridge/proxy/src/main/java/org/opennms/container/web/bridge/proxy/DispatcherTracker.java#L52) |
| ...and whiteboard servlets | [`ServletTracker.java:45`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/bridge/proxy/src/main/java/org/opennms/container/web/bridge/proxy/trackers/ServletTracker.java#L45) |
| REST paths are claimed by prefix | [`RestRequestHandler.java:44`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/bridge/proxy/src/main/java/org/opennms/container/web/bridge/proxy/handlers/RestRequestHandler.java#L44) |
| unclaimed requests continue down the chain | [`ProxyFilter.java:103`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/container/bridge/proxy/src/main/java/org/opennms/container/web/bridge/proxy/ProxyFilter.java#L103) |
| time series: `rrd` by default in the image | [`timeseries.properties.tmpl:7`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/confd/templates/timeseries.properties.tmpl#L7) |
| RRD files live in `/opennms-data/rrd` | [`Dockerfile:110`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L110) |
