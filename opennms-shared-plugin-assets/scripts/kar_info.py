#!/usr/bin/env python3
"""Look inside a Karaf archive (.kar) the way Karaf and the OpenNMS UI will.

    python3 scripts/kar_info.py plugins/node-inventory/assembly/kar/target/opennms-lab-node-inventory-plugin.kar
    python3 scripts/kar_info.py --json my-plugin.kar
    python3 scripts/kar_info.py --get extensions my-plugin.kar      # "id root module sha256" lines
    python3 scripts/kar_info.py --conflicts new.kar deploy/*.kar     # other KARs with the same features or ids

What it reports, and why it matters:
  * the KAR name: Karaf names an installed KAR after its file name without ".kar"
    (KarArtifactInstaller.getKarName), which is what "kar:list" shows;
  * Karaf-Feature-Start: unless the manifest says "false", installing the KAR also installs every
    feature in it whose install mode is "auto" (Kar.extract + KarServiceImpl.installFeatures);
  * the features and bundles in the KAR's repository/ folder;
  * every UIExtension service declared in a bundle's blueprint, with the module file OpenNMS
    will serve for it and that file's SHA-256 (scripts/deploy-plugin.sh compares it with what
    OpenNMS serves, to know when a new build is live).
Only the Python 3 standard library is used. Exit code 2 = not a readable KAR, 3 = conflicts found.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_plugins import blueprint_extensions  # noqa: E402  (same folder)

MANIFEST = "META-INF/MANIFEST.MF"


class KarError(Exception):
    pass


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_manifest(data: bytes) -> dict[str, str]:
    """Main section of a JAR manifest (continuation lines start with one space)."""
    headers: dict[str, str] = {}
    last = None
    for raw in data.decode("utf-8", errors="replace").splitlines():
        if not raw.strip():
            if headers:
                break  # end of the main section
            continue
        if raw.startswith(" ") and last:
            headers[last] += raw[1:]
        elif ":" in raw:
            key, _, value = raw.partition(":")
            last = key.strip()
            headers[last] = value.strip()
    return headers


def mvn_to_entry(url: str) -> str | None:
    """mvn:group/artifact/version[/type[/classifier]] -> repository/... path inside a KAR."""
    u = url.strip()
    for prefix in ("wrap:", "blueprint:", "webbundle:", "war:"):
        if u.startswith(prefix):
            u = u[len(prefix):]
    if not u.startswith("mvn:"):
        return None
    u = u[4:].split("$", 1)[0].split("?", 1)[0]
    if "!" in u:
        u = u.split("!", 1)[1]
    parts = u.split("/")
    if len(parts) < 3 or not all(parts[:3]):
        return None
    group, artifact, version = parts[:3]
    typ = parts[3] if len(parts) > 3 and parts[3] else "jar"
    classifier = parts[4] if len(parts) > 4 and parts[4] else None
    name = f"{artifact}-{version}" + (f"-{classifier}" if classifier else "") + f".{typ}"
    return f"repository/{group.replace('.', '/')}/{artifact}/{version}/{name}"


def entry_to_mvn(entry: str) -> str:
    """repository/org/x/art/1.0/art-1.0-features.xml -> mvn:org.x/art/1.0/xml/features (display only)."""
    parts = entry[len("repository/"):].split("/")
    if len(parts) < 4:
        return entry
    *group, artifact, version, filename = parts
    stem, _, typ = filename.rpartition(".")
    classifier = stem[len(f"{artifact}-{version}"):].lstrip("-") if stem.startswith(f"{artifact}-{version}") else ""
    return f"mvn:{'.'.join(group)}/{artifact}/{version}/{typ}" + (f"/{classifier}" if classifier else "")


def parse_features(data: bytes) -> list[dict]:
    root = ET.fromstring(data)
    features = []
    for f in root:
        if local(f.tag) != "feature":
            continue
        features.append({
            "name": f.get("name"),
            "version": f.get("version", "0.0.0"),
            "install": f.get("install") or "auto",
            "bundles": [b.text.strip() for b in f if local(b.tag) == "bundle" and b.text],
            "dependsOn": [(d.text or "").strip() for d in f if local(d.tag) == "feature"],
        })
    return features


def is_features_xml(data: bytes) -> bool:
    try:
        return local(ET.fromstring(data).tag) == "features"
    except ET.ParseError:
        return False


def blueprint_entries(names: list[str], header: str | None) -> list[str]:
    """Blueprint files of a bundle: Bundle-Blueprint if set, else OSGI-INF/blueprint/*.xml."""
    patterns = [p.split(";", 1)[0].strip() for p in header.split(",")] if header else ["OSGI-INF/blueprint/*.xml"]
    out = []
    for pat in patterns:
        pat = pat.lstrip("/")
        if pat.endswith("/"):
            pat += "*.xml"
        out += [n for n in names if fnmatch.fnmatchcase(n, pat) and n not in out]
    return out


def read_kar(path: str | Path, keep_bytes: bool = False) -> dict:
    path = Path(path)
    try:
        kar = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as e:
        raise KarError(f"{path}: not a readable KAR/zip file ({e})") from e
    with kar:
        names = kar.namelist()
        manifest = parse_manifest(kar.read(MANIFEST)) if MANIFEST in names else {}
        info: dict = {
            "file": str(path),
            "karName": path.name[: path.name.rfind(".")] if "." in path.name else path.name,
            # Kar.extract(): only the exact string "false" disables the feature installation
            "featureStart": manifest.get("Karaf-Feature-Start") != "false",
            "featureRepos": [],
            "features": [],
            "bundles": [],
            "extensions": [],
        }
        repo_xml = [n for n in names if n.startswith("repository/") and n.endswith(".xml")]
        if manifest.get("Karaf-Feature-Repos"):
            info["featureRepos"].append(manifest["Karaf-Feature-Repos"])
            entry = mvn_to_entry(manifest["Karaf-Feature-Repos"])
            feature_files = [entry] if entry in names else []
        else:
            feature_files = [n for n in repo_xml if is_features_xml(kar.read(n))]
            info["featureRepos"] = [entry_to_mvn(n) for n in feature_files]
        for ff in feature_files:
            info["features"] += parse_features(kar.read(ff))

        seen_bundles: set[str] = set()
        for feature in info["features"]:
            for url in feature["bundles"]:
                if url in seen_bundles:
                    continue
                seen_bundles.add(url)
                entry = mvn_to_entry(url)
                b = {"url": url, "entry": entry, "inKar": bool(entry and entry in names)}
                info["bundles"].append(b)
                if not b["inKar"]:
                    continue
                jar = zipfile.ZipFile(io.BytesIO(kar.read(entry)))
                jnames = jar.namelist()
                mf = parse_manifest(jar.read(MANIFEST)) if MANIFEST in jnames else {}
                b["symbolicName"] = mf.get("Bundle-SymbolicName", "").split(";", 1)[0].strip() or None
                b["version"] = mf.get("Bundle-Version")
                for bp in blueprint_entries(jnames, mf.get("Bundle-Blueprint")):
                    try:
                        exts = blueprint_extensions(io.BytesIO(jar.read(bp)))
                    except ET.ParseError as e:
                        b.setdefault("errors", []).append(f"{bp}: {e}")
                        continue
                    for ext in exts:
                        root = ext.get("resourceRootPath") or ""
                        module = ext.get("moduleFileName") or ""
                        mod_entry = f"{root}/{module}"
                        data = jar.read(mod_entry) if mod_entry in jnames else None
                        cls = ext.get("_class", "")
                        e = {
                            "extensionId": ext.get("extensionId"),
                            "menuEntry": ext.get("menuEntry"),
                            "resourceRootPath": root,
                            "moduleFileName": module,
                            "class": cls,
                            "classInBundle": cls.replace(".", "/") + ".class" in jnames,
                            "bundle": b["symbolicName"] or entry,
                            "blueprint": bp,
                            "moduleEntry": mod_entry,
                            "modulePresent": data is not None,
                            "moduleSize": len(data) if data is not None else None,
                            "moduleSha256": hashlib.sha256(data).hexdigest() if data is not None else None,
                            "styleCss": f"{root}/style.css" in jnames,
                            "usesArguments": bool(ext.get("_uses_arguments")),
                        }
                        if keep_bytes:
                            e["_module"] = data
                            e["_rootFiles"] = sorted(n[len(root) + 1:] for n in jnames
                                                     if root and n.startswith(root + "/") and not n.endswith("/")
                                                     and "/" not in n[len(root) + 1:])
                        info["extensions"].append(e)
        return info


def public(info: dict) -> dict:
    return {**info, "extensions": [{k: v for k, v in e.items() if not k.startswith("_")} for e in info["extensions"]]}


def conflicts(new: dict, others: list[dict]) -> list[tuple[str, str]]:
    """KARs (other file names) that ship a feature name or UI extension id the new KAR also ships."""
    feats = {f["name"] for f in new["features"]}
    ids = {e["extensionId"] for e in new["extensions"] if e["extensionId"]}
    found = []
    for o in others:
        if Path(o["file"]).name == Path(new["file"]).name:
            continue  # same file name = an update of the same KAR, not a conflict
        found += [(o["file"], f"feature {f['name']}") for f in o["features"] if f["name"] in feats]
        found += [(o["file"], f"UI extension id {e['extensionId']}") for e in o["extensions"] if e["extensionId"] in ids]
    return found


def describe(info: dict) -> str:
    out = [f"{info['file']}",
           f"  KAR name (kar:list)   {info['karName']}",
           f"  Karaf-Feature-Start   {'true: features are installed with the KAR' if info['featureStart'] else 'false: install the features yourself (feature:install)'}"]
    for f in info["features"]:
        flag = "" if f["install"] == "auto" else f"  (install={f['install']}: never installed automatically)"
        out.append(f"  feature               {f['name']}/{f['version']}{flag}")
    for b in info["bundles"]:
        where = f"{b.get('symbolicName') or '?'} {b.get('version') or ''}".strip() if b["inKar"] else "not in the KAR (must already exist in OpenNMS)"
        out.append(f"  bundle                {b['url']}  ->  {where}")
    if not info["extensions"]:
        out.append("  UI extensions         none (no <service interface=\"...UIExtension\"> in any bundle blueprint)")
    for e in info["extensions"]:
        state = f"{e['moduleSize']} bytes, sha256 {e['moduleSha256'][:12]}..." if e["modulePresent"] else "MISSING from the bundle"
        out.append(f"  UI extension          {e['extensionId']}  menu \"{e['menuEntry']}\"")
        out.append(f"                        module {e['moduleEntry']} ({state}); style.css {'yes' if e['styleCss'] else 'no'}")
        out.append(f"                        UI route #/plugins/{e['extensionId']}/{e['resourceRootPath']}/{e['moduleFileName']}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kar", nargs="+", help=".kar file(s)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--json", action="store_true", help="print a JSON array, one object per KAR")
    mode.add_argument("--get", choices=["karName", "featureStart", "features", "extensions", "bundles"],
                      help="print one field of the first KAR, in a shell-friendly form")
    mode.add_argument("--conflicts", action="store_true",
                      help="compare the first KAR with the others; exit 3 if they share features or extension ids")
    args = ap.parse_args()
    try:
        infos = [read_kar(k) for k in args.kar]
    except (KarError, KeyError, zipfile.BadZipFile, ET.ParseError) as e:
        print(f"kar_info: {e}", file=sys.stderr)
        return 2

    first = infos[0]
    if args.json:
        print(json.dumps([public(i) for i in infos], indent=2))
    elif args.get == "karName":
        print(first["karName"])
    elif args.get == "featureStart":
        print("true" if first["featureStart"] else "false")
    elif args.get == "features":
        for f in first["features"]:
            print(f"{f['name']}/{f['version']}")
    elif args.get == "bundles":
        for b in first["bundles"]:
            print(b["url"])
    elif args.get == "extensions":
        for e in first["extensions"]:
            print(e["extensionId"], e["resourceRootPath"], e["moduleFileName"], e["moduleSha256"] or "-")
    elif args.conflicts:
        found = conflicts(first, infos[1:])
        for file, what in found:
            print(f"{file}\t{what}")
        return 3 if found else 0
    else:
        print("\n\n".join(describe(i) for i in infos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
