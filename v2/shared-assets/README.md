# shared-assets

This folder is bind-mounted read-only into the OpenNMS container at
`/usr/share/opennms/jetty-webapps/opennms/assets/shared`, and Jetty serves it at:

```text
http://<opennms>:8980/opennms/assets/shared/<path in this folder>
```

Every UI plugin reads its icons and images from here. A file you add is served on the next
request; nothing needs a rebuild or a restart.

## Layout

| Path | Contents |
|---|---|
| `manifest.json` | the catalog plugins read: icon keys, other images, node-to-icon rules, `revision` |
| `manifest.schema.json` | JSON Schema for the catalog (editors use it for validation and completion) |
| `icons/` | node icons; a key without a catalog entry falls back to `icons/<key>.svg` |
| `branding/`, `images/`, ... | anything else, registered under `images` in the catalog |

Use lower-case names with letters, digits, `-`, `_` and `.`; no spaces.

## Adding or changing files

Preferred, from the repository root:

```bash
python3 scripts/assets.py add path/to/new.svg --key new-thing --label "New thing" [--category NewThings]
python3 scripts/assets.py validate
```

By hand, follow the same four rules the script follows:

1. **Atomic:** copy to a temporary name in the same directory, then `mv` it into place.
2. **Readable:** files `644`, directories `755` (OpenNMS reads them as uid 10001).
3. **Catalogued:** add the file to `manifest.json` if plugins should discover it.
4. **Revision:** increase `revision` whenever an existing file changes (`python3 scripts/assets.py bump`),
   so browsers stop using the copy they cached for up to one hour.

## Rules

* **Everything here is public.** OpenNMS lets anyone who reaches the web port read `/opennms/assets/**`.
* **Only trusted content.** An SVG opened directly runs as a page of the OpenNMS origin; clean SVGs from
  outside sources or convert them to PNG.
* **No symlinks to elsewhere on the host.** They resolve inside the container, where the target does not exist.

The icons in `icons/` and the banner in `branding/` were drawn for this lab and may be reused freely.
