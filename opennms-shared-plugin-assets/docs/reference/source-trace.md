# Reference: source trace

Every statement about OpenNMS, the Integration API, Jetty and Karaf in this guide rests on the lines
below. Links point at the exact tags: OpenNMS `opennms-33.1.8-1`, OIA `v1.6.1`, Jetty
`jetty-9.4.57.v20241219` (the version pinned by OpenNMS 33.1.8) and Karaf `karaf-4.3.10`. Line numbers
were computed from those tags when this guide was written.

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
| runs as uid 10001 | [`Dockerfile:155`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L155) |
| declared volumes | [`Dockerfile:169`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L169) |
| plugin KARs pre-installed in `deploy/` | [`Dockerfile:81`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/Dockerfile#L81) |
| overlay copied at start (not live) | [`entrypoint.sh:147`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L147) |
| `opennms.home` = `/usr/share/opennms` | [`entrypoint.sh:173`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/entrypoint.sh#L173) |
| database settings come from environment variables | [`opennms-datasources.xml.tmpl:20`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/opennms-container/core/container-fs/confd/templates/opennms-datasources.xml.tmpl#L20) |
| Jetty 9.4.57.v20241219 | [`pom.xml:1847`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/pom.xml#L1847) |
| Integration API 1.6.1 | [`pom.xml:1927`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/pom.xml#L1927) |
| Karaf 4.3.10 | [`pom.xml:1879`](https://github.com/OpenNMS/opennms/blob/opennms-33.1.8-1/pom.xml#L1879) |

## Integration API 1.6.1

| What | Where |
|---|---|
| "root path of UI extension web assets inside the bundle" | [`UIExtension.java:51`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/api/src/main/java/org/opennms/integration/api/v1/ui/UIExtension.java#L51) |
| "used to lookup OSGI bundle" | [`UIExtension.java:61`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/api/src/main/java/org/opennms/integration/api/v1/ui/UIExtension.java#L61) |
| scaffold externalises Vue, Pinia, vue-router | [`vite.config.ts:10`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/ui-extension/vite.config.ts#L10) |
| the scaffold imports an image... | [`App.vue:4`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/ui-extension/src/App.vue#L4) |
| ...which the build inlines as base64 | [`uiextension.es.js:1`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/sample/src/main/resources/ui-ext/uiextension.es.js#L1) |
| the archetype KAR does not auto-install its feature | [`pom.xml:32`](https://github.com/OpenNMS/opennms-integration-api/blob/v1.6.1/archetypes/example-kar-plugin/src/main/resources/archetype-resources/assembly/kar/pom.xml#L32) |

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
| bundle cache `${karaf.data}/cache` | [`ConfigProperties.java:298`](https://github.com/apache/karaf/blob/karaf-4.3.10/main/src/main/java/org/apache/karaf/main/ConfigProperties.java#L298) |
