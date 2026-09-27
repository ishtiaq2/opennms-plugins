# Part 8 - Moving your existing plugins to the shared folder

A checklist for plugins that currently import their images. Do it one plugin at a time; plugins
that already use the shared folder and plugins that still bundle their images can run side by side.

## 8.1 Collect the files

1. List the images each plugin imports (`grep -rn "assets/" src/` in each UI project, plus `url(`
   in styles).
2. Remove duplicates and copy one version of each file into `shared-assets/`, using the helper
   script so permissions and the catalog are right:

   ```bash
   python3 scripts/assets.py add ~/plugins/inventory/ui/src/assets/router.svg --key router --label Router
   python3 scripts/assets.py add ~/plugins/inventory/ui/src/assets/logo.png --kind image --as branding/logo.png --key logo
   python3 scripts/assets.py validate
   ```

3. Keep `shared-assets/` in version control. It is now a deliverable of its own, with its own
   owner and review process ([Part 5](05-design-decisions.md#54-security-notes)).

## 8.2 Add the helper to each plugin

The helper has no runtime dependencies and compiles into each plugin. Pick one:

* **Monorepo or workspace:** add `packages/shared-assets` as a workspace package (this repo's root
  `package.json` shows the npm workspaces setup) and depend on `"@onms-lab/shared-assets": "^1.0.0"`.
* **Separate repositories:** publish the package to your private npm registry, or install it from a
  path or Git URL (`npm install ../shared-assets`).
* **No build step change at all:** copy the four files in `packages/shared-assets/src/` into the
  plugin; they are plain TypeScript.

## 8.3 Replace imports with URLs

Before, the image travels inside the module as base64:

```vue
<script setup lang="ts">
import routerIcon from './assets/router.svg'
</script>
<template><img :src="routerIcon" alt="router" /></template>
```

After, the module only carries a URL:

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { EMPTY_MANIFEST, iconUrl, loadManifest, type SharedAssetsManifest } from '@onms-lab/shared-assets'

const manifest = ref<SharedAssetsManifest>(EMPTY_MANIFEST)
onMounted(async () => { manifest.value = await loadManifest() })
</script>
<template><img :src="iconUrl('router', manifest)" alt="router" /></template>
```

For node icons use `nodeIconUrl(node, manifest)` and move the "which icon for which node" logic
out of the plugins into `nodeIconRules`, so every plugin agrees. For a fixed file that is not in
the catalog, `assetUrl('branding/logo.png')` is enough.

**CSS.** Replace `background: url(./assets/bg.png)` with the absolute path
`url(/opennms/assets/shared/backgrounds/bg.png)`. Vite leaves absolute URLs it cannot resolve at
build time unchanged (it prints a notice), so check the built `style.css` to be sure.

## 8.4 Check the plugin contract

`scripts/check_plugins.py` accepts your bundle modules, or your built KARs, as arguments:

```bash
python3 scripts/check_plugins.py ~/plugins/inventory/plugin ~/plugins/topology/bundle
python3 scripts/check_plugins.py ~/plugins/inventory/assembly/kar/target/inventory.kar
```

It reads the `UIExtension` services from the blueprint files, understands the common property
names (`extensionId`/`id`, `resourceRootPath`/`resourceRoot`, ...), and checks the rules from
Part 3 against the built module. Given a KAR, it checks the bundle JARs inside it, which is exactly
what OpenNMS will load, and also reports `Karaf-Feature-Start: false` and features that Karaf will
not install automatically. It also warns when a module still contains large inlined images
and when the resource folder holds files the plugin endpoint cannot serve correctly.

Run against the OIA 1.6.1 `sample` module it produces a useful example of what it catches: the
sample's `RedPlugin.es.js` assigns `window["RedPlugin"]`, but its extension id is
`samplePluginOne`, and the 33.1.8 loader looks up non-legacy plugins under their extension id.
The sample's legacy `uiExtension` passes, with a warning for its inlined logo.

## 8.5 Rebuild, redeploy, verify

1. Build the module and the KAR as usual. The module should shrink by roughly 4/3 of the size of
   the images you removed.
2. Deploy the KAR with `scripts/deploy-plugin.sh <path to the KAR>` ([Part 6](06-installing-the-plugins.md#610-your-own-plugins));
   no OpenNMS configuration changes are needed.
3. Run `scripts/verify-assets.sh --plugins` and the Playwright test in `tests/e2e` (adjust the
   routes in `shared-assets.spec.ts` to your extension ids).
4. Open each plugin with the browser's developer tools and confirm that images load from
   `/opennms/assets/shared/` and that the console shows no CSP violations.

## 8.6 Versions to keep in step

| Item | 33.1.8 value | Where to look for another release |
|---|---|---|
| OIA version your bundle compiles against | 1.6.1 | `<opennmsApiVersion>` in the OpenNMS root `pom.xml` |
| Karaf (for `karaf-maven-plugin`) | 4.3.10 | `<karafVersion>` in the same file |
| Vue runtime your module runs on | 3.3.7 | `vue@^3...` entry in `ui/yarn.lock` |
| Jetty behaviour described in Part 4 | 9.4.57.v20241219 | `<jettyVersion>` |

A bundle compiled against OIA 1.6.1 imports its packages with the range `[1.6,2)`, so it will not
resolve on an OpenNMS whose Integration API is 2.x; rebuild it with `OIA_VERSION=<version>
scripts/build-plugins.sh` for such releases.
