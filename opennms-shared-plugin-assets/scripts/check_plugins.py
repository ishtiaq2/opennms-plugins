#!/usr/bin/env python3
"""Check UI-extension plugins against the contract the OpenNMS 33.1.8 UI expects.

    python3 scripts/check_plugins.py                       # the demo plugins in this repo
    python3 scripts/check_plugins.py ~/src/my-plugin/plugin ~/src/other-plugin/bundle

Each argument is a Maven bundle module: the directory with src/main/resources/OSGI-INF/blueprint/
and src/main/java/. If a Vite project sits next to it (../ui/vite.config.ts) or inside it
(ui/vite.config.ts) and defines EXTENSION_ID / RESOURCE_ROOT / MODULE_FILE constants, those are
compared with blueprint.xml as well.

Run it after building the JS module (scripts/build-plugins.sh does). Every rule comes from the
OpenNMS or OIA source; docs/reference/source-trace.md cites the exact files.
Exit code 0 = no FAIL (WARNs allowed), 1 = at least one FAIL.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_EXTENSION = "org.opennms.integration.api.v1.ui.UIExtension"
BP_NS = "{http://www.osgi.org/xmlns/blueprint/v1.0.0}"
# ui/src/router/index.ts + ui/src/components/Plugin/utils.ts treat these as "legacy" plugins
LEGACY_IDS = {"cloudUiExtension", "uiextension", "uiExtension"}

ALIASES = {
    "extensionId": ("extensionId", "id", "extensionID"),
    "menuEntry": ("menuEntry", "menu", "menuName"),
    "resourceRootPath": ("resourceRootPath", "resourceRoot", "rootPath"),
    "moduleFileName": ("moduleFileName", "moduleFile", "moduleName"),
}

results: list[tuple[str, str, str]] = []


def report(level: str, plugin: str, msg: str) -> None:
    results.append((level, plugin, msg))


def blueprint_extensions(bp: Path) -> list[dict[str, str]]:
    tree = ET.parse(bp)
    found = []
    for svc in tree.getroot().iter(f"{BP_NS}service"):
        if svc.get("interface") != UI_EXTENSION:
            continue
        bean = svc.find(f"{BP_NS}bean")
        if bean is None:
            continue
        raw = {p.get("name"): p.get("value") for p in bean.findall(f"{BP_NS}property")}
        # Property names are whatever the implementation's setters are called; the OIA sample
        # uses "id" and "resourceRoot", this repo uses the interface's names.
        props = {}
        for canonical, aliases in ALIASES.items():
            props[canonical] = next((raw[a] for a in aliases if raw.get(a)), None)
        props["_class"] = bean.get("class", "")
        props["_uses_arguments"] = bean.find(f"{BP_NS}argument") is not None
        found.append(props)
    return found


def vite_constants(cfg: Path) -> dict[str, str]:
    text = cfg.read_text(encoding="utf-8")
    out = {}
    for name in ("EXTENSION_ID", "RESOURCE_ROOT", "MODULE_FILE"):
        m = re.search(rf"const {name} = '([^']*)'", text)
        if m:
            out[name] = m.group(1)
    return out


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def check_plugin(bundle: Path, seen_ids: dict[str, str]) -> None:
    name = bundle.parent.name if bundle.name in ("plugin", "bundle") else bundle.name
    bp_dir = bundle / "src/main/resources/OSGI-INF/blueprint"
    blueprints = sorted(bp_dir.glob("*.xml")) if bp_dir.is_dir() else []
    if not blueprints:
        # Bundles may name their files with a Bundle-Blueprint header instead (the OIA sample does).
        res = bundle / "src/main/resources"
        blueprints = sorted(x for x in res.glob("*.xml") if "<blueprint" in x.read_text(encoding="utf-8", errors="ignore")) if res.is_dir() else []
    if not blueprints:
        report("FAIL", name, f"no blueprint XML in {rel(bp_dir)} or {rel(bundle / 'src/main/resources')}")
        return
    exts = [e for bp in blueprints for e in blueprint_extensions(bp)]
    if not exts:
        report("FAIL", name, f"no <service interface=\"{UI_EXTENSION}\"> in {rel(bp_dir)}/*.xml")
        return
    for ext in exts:
        if ext["_uses_arguments"] and not ext.get("extensionId"):
            report("WARN", name, f"{ext['_class']} is configured with constructor arguments; this checker only reads <property> values")
            continue
        ext_id = ext.get("extensionId") or ""
        root = ext.get("resourceRootPath") or ""
        module = ext.get("moduleFileName") or ""
        label = f"{name}/{ext_id or '?'}"

        # --- identity ---------------------------------------------------------------
        if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", ext_id):
            report("FAIL", label, "extensionId must be a plain identifier: it becomes window[extensionId] and a URL path segment")
        elif ext_id in seen_ids:
            report("FAIL", label, f"extensionId also used by {seen_ids[ext_id]} (UIExtensionRegistryImpl keeps only one per id)")
        else:
            seen_ids[ext_id] = name
            report("PASS", label, "extensionId is a unique identifier")
        if ext_id in LEGACY_IDS:
            report("WARN", label, "this extensionId is treated as a legacy plugin by the OpenNMS UI")

        # --- resourceRootPath -------------------------------------------------------------
        if not root or re.search(r"[/\\?#]", root):
            report("FAIL", label, f"resourceRootPath '{root}' must be ONE path segment (UI route /plugins/:id/:resourceRootPath/:moduleFileName)")
        else:
            report("PASS", label, f"resourceRootPath '{root}' is a single segment")

        # --- moduleFileName ---------------------------------------------------------------
        if not re.match(r"^(.*?)\.es", module) or not module.endswith(".js") or "/" in module:
            report("FAIL", label, f"moduleFileName '{module}' must look like <name>.es.js (the UI parses it with /^(.*?)\\.es/)")
        else:
            report("PASS", label, f"moduleFileName '{module}' matches the UI's parser")

        # --- Java class lives in this bundle -------------------------------------------------
        cls = ext.get("_class", "")
        java = bundle / "src/main/java" / (cls.replace(".", "/") + ".java")
        if not java.exists():
            report("FAIL", label, f"bean class {cls} not found in this plugin's sources (getExtensionClass() must come from this bundle)")
        else:
            src = java.read_text(encoding="utf-8")
            if "implements UIExtension" not in src:
                report("FAIL", label, f"{cls} does not implement UIExtension")
            elif not re.search(r"getExtensionClass\(\)\s*\{\s*return\s+(getClass\(\)|this\.getClass\(\)|\w+\.class)\s*;", src):
                report("WARN", label, "getExtensionClass() should return a class of THIS bundle (e.g. getClass())")
            else:
                report("PASS", label, f"{cls.rsplit('.', 1)[-1]} is in this bundle and returns its own class")

        # --- vite.config.ts agrees with blueprint -------------------------------------------
        cfg = next((c for c in (bundle.parent / "ui/vite.config.ts", bundle / "ui/vite.config.ts") if c.exists()), None)
        if cfg is not None and vite_constants(cfg):
            c = vite_constants(cfg)
            want = {"EXTENSION_ID": ext_id, "RESOURCE_ROOT": root, "MODULE_FILE": module}
            diff = {k: (c.get(k), v) for k, v in want.items() if c.get(k) != v}
            if diff:
                report("FAIL", label, f"{rel(cfg)} disagrees with blueprint.xml: {diff}")
            else:
                report("PASS", label, "vite.config.ts and blueprint.xml agree")

        # --- built module ----------------------------------------------------------------------
        res_dir = bundle / "src/main/resources" / root
        mod = res_dir / module
        if not mod.exists():
            report("FAIL", label, f"{rel(mod)} not built yet (build the JS module first)")
            continue
        data = mod.read_bytes()
        text = data.decode("utf-8", errors="replace")
        # Same rule as externalComponent() in ui/src/components/Plugin/utils.ts: legacy plugins are
        # looked up under the module name, every other plugin under its extension id.
        stem_match = re.match(r"^(.*?)\.es", module)
        stem = stem_match.group(1) if stem_match else ""
        key = stem if (stem == "uiextension" and ext_id in LEGACY_IDS) else ext_id
        if re.search(rf"window(\.{re.escape(key)}|\[\s*['\"]{re.escape(key)}['\"]\s*\])\s*=", text):
            report("PASS", label, f"module assigns window.{key} (the key the UI reads)")
        else:
            report("FAIL", label, f"module never assigns window['{key}'] - the UI would render nothing")
        if re.search(r"^\s*import\s[^;]*from\s*['\"](vue|pinia|vue-router)['\"]", text, re.M):
            report("FAIL", label, "module still imports vue/pinia/vue-router; use the window.Vue externals")
        elif "__v_isRef" in text:
            # marker of @vue/reactivity: present when Vue is bundled, absent with the window.Vue externals
            report("FAIL", label, "module bundles its own Vue runtime (found '__v_isRef'); externalise vue, pinia and vue-router")
        else:
            report("PASS", label, "uses the host's window.Vue (no Vue imports, no bundled Vue runtime)")
        if re.search(r"\bprocess\.env\b", text):
            report("FAIL", label, "module references process.env (undefined in browsers)")
        if any(b > 0x7F for b in data):
            report("WARN", label, "module has non-ASCII bytes; UIExtensionServiceImpl decodes it with the JVM default charset")
        else:
            report("PASS", label, "module is ASCII-only (safe for new String(bytes) on the server)")
        inlined = re.findall(r"data:image/[a-z+.-]+;base64,[A-Za-z0-9+/=]{2000,}", text)
        if inlined:
            report("WARN", label, f"{len(inlined)} large inlined image(s) in the module - move them to the shared folder")
        if not (res_dir / "style.css").exists():
            report("WARN", label, f"{root}/style.css missing - the UI always requests /rest/plugins/ui-extension/css/{ext_id}")
        binaries = [p.name for p in res_dir.iterdir()
                    if p.is_file() and not p.name.startswith(".") and p.suffix.lower() not in {".js", ".css", ".map"}]
        if binaries:
            report("WARN", label, f"files the plugin endpoint cannot serve correctly: {binaries} (it only returns the module as application/javascript and style.css)")


def main() -> int:
    if len(sys.argv) > 1:
        plugins = [Path(a).expanduser().resolve() for a in sys.argv[1:]]
    else:
        plugins = sorted(p / "plugin" for p in (ROOT / "plugins").iterdir() if (p / "plugin").is_dir())
    seen: dict[str, str] = {}
    for p in plugins:
        check_plugin(p, seen)
    width = max(len(r[1]) for r in results) if results else 10
    for level, plugin, msg in results:
        print(f"{level:4}  {plugin:<{width}}  {msg}")
    fails = sum(1 for r in results if r[0] == "FAIL")
    warns = sum(1 for r in results if r[0] == "WARN")
    print(f"\n{len(plugins)} plugin(s): {fails} FAIL, {warns} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
