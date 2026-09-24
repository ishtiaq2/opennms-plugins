# Part 5 - Design decisions and the alternatives

This part records why the lab serves the shared folder the way it does, what else would work, and
what each option costs. Every option below was either traced in the source or run in the test
harness; the "verified" column says which.

## 5.1 The decision

> Keep one folder of shared UI files on the host. Bind-mount it read-only at
> `$OPENNMS_HOME/jetty-webapps/opennms/assets/shared`. Let the `opennms` web application's own
> `DefaultServlet` serve it at `/opennms/assets/shared/`. Plugins reference files by URL and
> discover them through `manifest.json`.

It meets all four constraints from Part 1 with no code and no configuration change in OpenNMS:
same origin as the UI (CSP passes), correct content types (Jetty's MIME table), readable by the
plugin's page (Spring Security permits `/assets/**`), and live (bind mount plus Jetty's cache
validation). As a bonus it inherits OpenNMS's own caching policy for static assets.

## 5.2 The options side by side

| | A. `assets/shared` mount (**chosen**) | B. mount outside `assets/` | C. extra context in `etc/jetty.xml` | D. directory in `jetty-webapps/` | E. OSGi bundle serving files |
|---|---|---|---|---|---|
| URL | `/opennms/assets/shared/` | e.g. `/opennms/shared-assets/` | e.g. `/nms-shared/` | `/<dir name>/` | e.g. `/opennms/shared-assets/` or `/opennms/rest/...` |
| Code / config | one volume line | one volume line | replace the whole `jetty.xml` | one volume line | a Java bundle |
| Login required | no | yes (`/**` needs `ROLE_USER`) | no (outside Spring Security) | no | yes |
| Browser caching | `max-age=3600,public` | `no-store` (RewriteHandler) | your choice (e.g. `no-cache` + ETag) | none sent | your choice (must override `no-store`) |
| Live on drop | yes | yes | yes | yes, but top-level changes redeploy the context | depends on the code |
| Directory listing | off (`403`) | off (`403`) | your choice | **on** (Jetty default) | your choice |
| Survives OpenNMS upgrades | yes, as long as the webapp stays at `jetty-webapps/opennms` | same | you must merge each new `jetty.xml` | yes | rebuild against the new OIA |
| Verified | source + harness | source (Spring Security rules, RewriteHandler) | harness | harness | not built here |

### B. A login-protected folder with no code

Mount the same folder at `/usr/share/opennms/jetty-webapps/opennms/shared-assets` instead. Spring
Security's catch-all `<intercept-url pattern="/**" access="hasAnyRole('ROLE_USER')"/>` then
applies, so only logged-in users can read it, and the plugins' `<img>` requests carry the session
cookie anyway. The price is the RewriteHandler's `Cache-Control: no-store` for everything under
`/opennms/` except `assets/`: the browser fetches every icon again on every page load. Pass
`base: '/opennms/shared-assets/'` to the helper functions if you choose this.

### C. An extra Jetty context in a custom `etc/jetty.xml`

Copy `etc/examples/jetty.xml` to `etc/jetty.xml` (with the `etc` overlay this is
`etc-overlay/jetty.xml`) and add a context next to the web applications. This fragment goes after
the `Handlers` definition and before `<Set name="handler">`:

```xml
<Ref refid="Contexts">
  <Call name="addHandler">
    <Arg>
      <New class="org.eclipse.jetty.server.handler.ContextHandler">
        <Set name="contextPath">/nms-shared</Set>
        <Set name="handler">
          <New class="org.eclipse.jetty.server.handler.ResourceHandler">
            <Set name="resourceBase">/opt/nms-shared-assets</Set>
            <Set name="dirAllowed">false</Set>
            <Set name="etags">true</Set>
            <Set name="cacheControl">no-cache</Set>
          </New>
        </Set>
      </New>
    </Arg>
  </Call>
</Ref>
```

and mount the folder at `/opt/nms-shared-assets`. In the harness this answered with a weak
`ETag`, `Cache-Control: no-cache`, `304` on `If-None-Match`, and `403` for directories, while the
`/opennms` application kept working. `no-cache` means "revalidate every time", so even a replaced
file is visible on the next page load without a revision bump.

The costs: `JettyServer` reads *either* `etc/jetty.xml` *or* the built-in file, so from now on you
own a full copy and must merge OpenNMS's changes at every upgrade. The context sits outside the
`opennms` web application, so none of its filters or security run: no CSP, no `nosniff`, no
Spring Security. A reverse proxy that forwards only `/opennms/` needs a new rule for the new
prefix.

### D. A directory in `jetty-webapps/`

Mounting the folder at `$OPENNMS_HOME/jetty-webapps/nms-assets` needs no configuration: the
deployment manager scans that directory every 10 seconds and deployed it as the context
`/nms-assets` about 15 seconds after it appeared in the harness. Three things make it a poor
choice:

* the new context uses Jetty's stock `webdefault.xml`, where `dirAllowed` is `true`: anyone can
  list the folder;
* no `Cache-Control` header is sent at all, so browsers fall back to heuristic caching;
* the scanner watches the modification time of each directory directly in `jetty-webapps/`.
  Adding a file at the top level of the folder changes that time, and Jetty stopped and restarted
  the whole context (about 20 seconds later in the harness). Files in sub-directories do not
  trigger this.

### E. An OSGi bundle that serves the files

The `ProxyFilter` described in Part 3 forwards requests to OSGi HTTP-whiteboard servlets
(`osgi.http.whiteboard.servlet.pattern`) and whiteboard resources
(`osgi.http.whiteboard.resource.pattern` plus `...resource.prefix`), and JAX-RS services with
`application-path=/rest` become REST endpoints. A small bundle could therefore serve a host folder
behind Spring Security with any headers you like and a real listing API. That is the right tool
if you need access control and caching at the same time, or per-user filtering. It is also
Java code to build, test and upgrade with every OIA release, and it has to override the `no-store`
header the RewriteHandler sets on its responses. Whiteboard *resources* serve files packed inside
a bundle, so on their own they would not meet the "drop a file on the host" requirement.

## 5.3 Caching policy: one hour plus a revision

Under `/opennms/assets/` browsers may reuse a file for an hour without asking. That is ideal for
icons that rarely change, and it would be a problem the day you fix an icon, because some browsers
would keep the old one for up to an hour. The manifest's `revision` solves it: every URL the
helper builds carries `?rev=<revision>`, the browser treats a new query string as a new resource,
and `manifest.json` itself is revalidated on every page load (`fetch` with `cache: 'no-cache'`,
answered with `304` when unchanged). So:

* new file: visible at once, no revision bump needed;
* changed file: bump the revision (`scripts/assets.py add` and `scripts/assets.py bump` do it);
* the cost of a bump: every client downloads each icon once more.

## 5.4 Security notes

**Public.** Everything in the folder is readable without logging in, like OpenNMS's own
JavaScript. Do not put anything sensitive in it.

**Trusted content only.** Browsers never run scripts inside an SVG loaded with `<img>`. But the
same SVG opened directly (a user clicks its URL) is a document on the OpenNMS origin, and the web
application's CSP allows inline scripts (`script-src 'self' 'unsafe-inline' 'unsafe-eval'`). A
malicious SVG in the folder could therefore run JavaScript as the OpenNMS origin. Treat write
access to the host folder like write access to OpenNMS's configuration, and clean SVGs from
outside sources (strip `<script>` and event attributes, for example with `svgo`) or convert them
to PNG.

**Read-only.** The mount is `:ro`. Nothing inside the container, OpenNMS included, can change the
folder; only the host can.

## 5.5 Beyond one container

* **Several OpenNMS instances:** mount the same folder from shared storage (NFS) or distribute it
  with `rsync`; the URL contract stays the same.
* **Immutable images:** for production you may prefer to bake the files into a derived image
  (`FROM opennms/horizon:33.1.8` plus `COPY shared-assets /usr/share/opennms/jetty-webapps/opennms/assets/shared`).
  You lose "live" and gain reproducibility; the plugins do not notice the difference.
* **Kubernetes:** mount a volume at the same path. A ConfigMap works for small icon sets (a
  ConfigMap is limited to 1 MiB); anything bigger belongs on a persistent volume.
* **Reverse proxies:** keep the files on the same origin as the UI. A proxy that forwards
  `/opennms/` already forwards `/opennms/assets/shared/`.

## 5.6 Deploying plugins: a second deploy folder

The shared folder answers "where do the images go". The plugins themselves arrive as KARs, and in
a container the place you put a KAR decides two things: whether installing a plugin is a file copy
on the host, and whether the plugin is still there after the container is re-created (a new image
version, `podman-compose down` and `up`). `$OPENNMS_HOME/data/`, where Karaf keeps its KAR and
bundle caches and its record of installed features, is not a volume in the Horizon image.

| | **`./deploy` + second watcher (chosen)** | `podman cp` into `$OPENNMS_HOME/deploy` | `kar:install` in the Karaf shell | `/opt/opennms-overlay/deploy/` | host folder mounted over `$OPENNMS_HOME/deploy` |
|---|---|---|---|---|---|
| Install | copy a file on the host | `podman cp` | a shell command; the file must be reachable inside the container | copy, then restart | copy a file on the host |
| Live, no restart | yes, within a second | yes | yes | no: copied at start | yes |
| Uninstall | delete the file | `podman exec ... rm` | `kar:uninstall` | delete it, then re-create the container (the copy in `deploy/` stays until then) | delete the file |
| After re-creating the container | re-installed from the mount at start | gone | gone | re-installed | re-installed |
| KARs shipped in the image (Cortex TSS, VeloCloud) | untouched | untouched | untouched | untouched | hidden by the mount |
| Extra configuration | one `.cfg` file, through the etc overlay | none | none | none | none |

The chosen option relies on standard Karaf behaviour: Felix FileInstall reads every
`etc/org.apache.felix.fileinstall-<name>.cfg` as the configuration of one more watched folder
(Karaf's own `deploy/` is configured by `etc/org.apache.felix.fileinstall-deploy.cfg` in exactly
this way), and any `.kar` file a watcher finds goes to the same KAR deployer. The lab's file copies
Karaf's settings for `deploy/` (poll every second, start at start level 80) and changes three:
the directory, a separate temporary directory, and a filter that accepts only `*.kar`, so that a
README or a half-copied `.part` file is never touched. It is read-only in the container, like the
shared folder: only the host can add or remove plugins.

The version of this lab before this one used the overlay (`/opt/opennms-overlay/deploy/`). It
works, but every plugin change needed a restart, and removing a plugin needed a re-created
container, because the entrypoint's `rsync` copies files but never deletes them.

These behaviours are traced to the Karaf 4.3.10, Felix FileInstall 3.7.4 and Horizon entrypoint
sources in the [source trace](reference/source-trace.md); how the deploy scripts were exercised
is in [verification](reference/verification.md).
