# Part 8 - Troubleshooting

Work from the outside in: first the file on the host, then the HTTP response, then the plugin.
`scripts/assets.py validate` checks the folder, `scripts/verify-assets.sh` checks what Jetty
answers, and `scripts/check_plugins.py` checks a plugin build.

## The shared folder

| Symptom | Likely cause | Fix |
|---|---|---|
| Every shared URL returns `404` | the folder is not mounted where Jetty looks | the target must be `/usr/share/opennms/jetty-webapps/opennms/assets/shared`; check with `podman exec <container> ls /usr/share/opennms/jetty-webapps/opennms/assets/shared` |
| One file returns `404`, it exists on the host | file not readable by uid 10001, or it sits in a directory without `o+x` | `chmod 644` the file, `chmod 755` the directories; `assets.py validate` lists them |
| `ls` inside the container says "Permission denied" | SELinux label | add `z` to the mount options (already in `compose.yml`) |
| The folder listing returns `403` | `dirAllowed=false` in OpenNMS's `web.xml` | expected; use `manifest.json` |
| A symlinked file gives an empty reply or `404` | the link target does not exist inside the container | copy the file instead of linking it |
| The container stops at start with an `rsync` error | the overlay contains files for `jetty-webapps/opennms/assets/shared/`, which is a read-only mount | keep shared files out of `overlay/` |
| A file shows up broken (half an image) | it was written in place while being served | write to a temporary name and rename, as `assets.py add` does |

## The HTTP response

| Symptom | Likely cause | Fix |
|---|---|---|
| The old version of a replaced icon keeps showing | the browser's cache (`max-age=3600`) | `python3 scripts/assets.py bump` and reload |
| `Cache-Control: no-store` on a shared file | the file is served from outside `/opennms/assets/` (option B), or a custom `etc/jetty.xml` changed the rule | mount under `assets/`, or accept `no-store` |
| An SVG downloads instead of displaying when opened directly | wrong extension, so no `image/svg+xml` type | files need a known extension (`.svg`, `.png`, `.webp`, ...) |
| `401`/`302` to the login page for a shared file | the folder is mounted outside `/assets/` and you are not logged in | expected for option B; for option A check the URL |

## The plugin

| Symptom | Likely cause | Fix |
|---|---|---|
| The plugin is missing from the **Plugins** menu and from `/opennms/rest/plugins` | KAR not deployed, feature not installed, or bundle not active | Karaf shell: `kar:list`, `feature:list \| grep opennms-lab`, `bundle:list`, `bundle:diag <id>` |
| Two plugins, one menu entry | both use the same `extensionId` | ids must be unique; `check_plugins.py` checks this across the plugins you pass it |
| Console: "Errors with component url." | `moduleFileName` without `.es`, or a `resourceRootPath` containing `/` | see Part 3 and `check_plugins.py` |
| The page stays empty, no console error | the module assigns a different `window[...]` key than the loader reads | `window[extensionId] = Component` (legacy plugins excepted) |
| `ReferenceError: process is not defined` | library mode left `process.env.NODE_ENV` in the module | `define: { 'process.env.NODE_ENV': JSON.stringify('production') }` in `vite.config.ts` |
| Vue warnings about invalid vnodes, or reactivity that never updates | the module bundles its own Vue | externalise `vue`, `pinia`, `vue-router` to the `window` globals |
| Text with `?` or garbage characters | non-ASCII characters in the module, decoded with the JVM default charset | keep the module ASCII-only; `check_plugins.py` warns |
| Console: "Refused to load the image ... Content Security Policy" | the image URL has another origin (host name, port or scheme) | use root-relative URLs (`/opennms/assets/shared/...`), which the helper builds |
| All icons show the default icon | `manifest.json` not loaded (network error, invalid JSON) | open it in the browser; the helper logs `[shared-assets] manifest unavailable` |
| The plugin module is re-downloaded on every page load | `/opennms/rest/...` responses carry `Cache-Control: no-store` | expected; that is OpenNMS's policy for everything outside `/opennms/assets/` |
