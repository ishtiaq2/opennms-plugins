# Part 1 - Why every plugin ends up with its own copy of the images

Before fixing anything it helps to see why the duplication happens in the first place. It is not
an accident of how your plugins were written; it follows directly from how OpenNMS 33.1.8 loads
UI extensions. Once the mechanism is clear, the fix in the later parts will look obvious.

## 1.1 What a UI extension actually ships

An Integration API (OIA) UI extension is an OSGi bundle (a JAR) that contains three things:

| Inside the JAR | Purpose |
|---|---|
| a class implementing `org.opennms.integration.api.v1.ui.UIExtension` | tells OpenNMS the extension id, the menu label, the folder and the file name of the JavaScript module |
| `OSGI-INF/blueprint/blueprint.xml` | registers that class as an OSGi service |
| `<resourceRootPath>/<moduleFileName>` and `<resourceRootPath>/style.css` | the Vue module built by Vite, and its CSS |

The interface has exactly five methods (`getExtensionId`, `getMenuEntry`, `getResourceRootPath`,
`getModuleFileName`, `getExtensionClass`); its Javadoc describes `getResourceRootPath()` as "the
root path of UI extension web assets inside the bundle". So the design assumption is that
everything a plugin needs travels inside its own bundle.

## 1.2 How OpenNMS serves what is inside the bundle

OpenNMS core publishes one REST resource for all UI extensions, `UIExtensionServiceImpl`
(module `features/ui-extension`), mounted under `/opennms/rest/plugins`. It has exactly three
operations:

| Request | What the code does | Response type |
|---|---|---|
| `GET /opennms/rest/plugins` | lists every registered `UIExtension` | JSON |
| `GET /opennms/rest/plugins/ui-extension/module/{id}?path=<p>` | `FrameworkUtil.getBundle(ext.getExtensionClass()).getResource(p)`, then `new String(bytes)` | always `application/javascript` |
| `GET /opennms/rest/plugins/ui-extension/css/{id}` | same lookup for the fixed path `<resourceRootPath>/style.css` | always `text/css` |

There is no endpoint for "any other file in my bundle". You can point the module endpoint at a
PNG (`?path=my-root/logo.png`), but the file is turned into a Java `String` with the JVM's default
charset and sent back labelled `application/javascript`. In this lab's test harness, which
reproduces that code path, a 9,737-byte PNG came back as 17,490 bytes of mangled text, and neither
that PNG nor an SVG requested the same way rendered in Chromium (see
[reference/verification.md](reference/verification.md), browser check 8).

Relative URLs do not rescue you either. The browser loads your module from
`/opennms/rest/plugins/ui-extension/module/<id>?path=...`, so `new URL('./logo.png', import.meta.url)`
resolves to `/opennms/rest/plugins/ui-extension/module/logo.png`, a URL the module endpoint cannot
answer with an image.

## 1.3 So the build tool inlines the images

Plugin modules are built with Vite in *library mode* (the OIA `ui-extension` scaffold uses
`build.lib` with a single ES module output). In library mode Vite inlines every imported asset as a
base64 `data:` URI, whatever its size. The OIA 1.6.1 repository shows it: the `ui-extension`
scaffold's `App.vue` has `<img src="./assets/logo.png">`, and the built copy shipped in the `sample`
bundle (`ui-ext/uiextension.es.js`) starts with `var _imports_0 = "data:image/png;base64,iVBORw0KGgo..."`.
A quick check with Vite 5.4.21 inlined a 49 KB PNG, far above the default 4 KB `assetsInlineLimit`.

This works in OpenNMS because the Content-Security-Policy of the web UI allows `data:` images:

```text
img-src 'self' https://tiles.opennms.org https://*.tile.openstreetmap.org https://*.tile.opentopomap.org data:
```

But look at the cost when two or more plugins show the same node icons:

* every plugin carries its own base64 copy (about a third larger than the file itself);
* changing an icon means rebuilding and redeploying every plugin that uses it;
* nobody outside the plugin build (an operator, a designer) can add an icon.

That is the situation this lab sets out to fix.

## 1.4 The constraints any fix has to respect

The same source files that explain the problem also fence in the solution:

1. **Same origin.** The CSP above only allows images from `'self'` (plus `data:` and three map
   tile hosts). A separate web server on another port or host would be blocked, unless a reverse
   proxy puts it on the same origin. The harness shows Chromium refusing an image from
   `http://127.0.0.1:8980` on a page served from `http://localhost:8980`.
2. **Served with the right Content-Type.** An `<img>` needs `image/svg+xml`, `image/png` and so
   on, so the files must be served by something that knows file types. Jetty's `DefaultServlet`
   does.
3. **Readable by the browser session that renders the plugin.** The plugin runs inside the new UI
   at `/opennms/ui/`, logged in with the `JSESSIONID` cookie, and Spring Security decides per URL
   pattern who may read what.
4. **Live.** You want to drop a file on the host and have the plugins see it, with no rebuild, no
   `podman exec`, no restart.

[Part 2](02-where-assets-live.md) maps every place a file can live in an OpenNMS container and
shows which of them meets all four constraints.
