"""Unit tests for the repository's Python and shell tooling (standard library only).

    python3 -m unittest discover -s tests/scripts -v

The KARs built here follow the layout of karaf-maven-plugin's "kar" goal: META-INF/MANIFEST.MF with
Karaf-Feature-Start, the features XML and the bundle JAR in Maven layout under repository/. The
bundle holds the demo plugin's real blueprint.xml and built Vue module from this repository.
"""
from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import check_plugins  # noqa: E402
import kar_info  # noqa: E402

G, V = "org/example/opennms/lab", "1.0.0-SNAPSHOT"


def build_kar(dest: Path, plugin: str = "node-inventory", feature_start: str | None = "true",
              module_edit=None) -> Path:
    res = REPO / "plugins" / plugin / "plugin/src/main/resources"
    jar = io.BytesIO()
    with zipfile.ZipFile(jar, "w") as z:
        z.writestr("META-INF/MANIFEST.MF", f"Manifest-Version: 1.0\r\nBundle-SymbolicName: lab.{plugin}\r\n"
                                           "Bundle-Version: 1.0.0.SNAPSHOT\r\n\r\n")
        for f in sorted(res.rglob("*")):
            if f.is_file():
                data = f.read_bytes()
                if module_edit and f.name.endswith(".es.js"):
                    data = module_edit(data)
                z.writestr(f.relative_to(res).as_posix(), data)
        bp = (res / "OSGI-INF/blueprint/blueprint.xml").read_text(encoding="utf-8")
        cls = bp.split('<bean class="', 1)[1].split('"', 1)[0]
        z.writestr(cls.replace(".", "/") + ".class", b"\xca\xfe\xba\xbe")
    features = (REPO / "plugins" / plugin / "karaf-features/src/main/resources/features.xml").read_text(encoding="utf-8")
    features = features.replace("${project.version}", V).replace("${opennms.api.version}", "1.6.1")
    manifest = "Manifest-Version: 1.0\r\n" + (f"Karaf-Feature-Start: {feature_start}\r\n" if feature_start else "") + "\r\n"
    with zipfile.ZipFile(dest, "w") as z:
        z.writestr("META-INF/MANIFEST.MF", manifest)
        fa = f"{plugin}-karaf-features"
        z.writestr(f"repository/{G}/{fa}/{V}/{fa}-{V}-features.xml", features)
        z.writestr(f"repository/{G}/{fa}/{V}/maven-metadata-local.xml", "<metadata/>")
        z.writestr(f"repository/{G}/{plugin}-plugin/{V}/{plugin}-plugin-{V}.jar", jar.getvalue())
    return dest


class KarInfoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_reads_what_karaf_and_the_ui_will_use(self):
        info = kar_info.read_kar(build_kar(self.tmp / "opennms-lab-node-inventory-plugin.kar"))
        self.assertEqual(info["karName"], "opennms-lab-node-inventory-plugin")
        self.assertTrue(info["featureStart"])
        self.assertEqual([f["name"] for f in info["features"]], ["opennms-lab-node-inventory"])
        self.assertEqual(info["featureRepos"], [f"mvn:org.example.opennms.lab/node-inventory-karaf-features/{V}/xml/features"])
        self.assertTrue(info["bundles"][0]["inKar"])
        (ext,) = info["extensions"]
        self.assertEqual((ext["extensionId"], ext["resourceRootPath"], ext["moduleFileName"]),
                         ("labNodeInventory", "node-inventory", "nodeInventory.es.js"))
        module = REPO / "plugins/node-inventory/plugin/src/main/resources/node-inventory/nodeInventory.es.js"
        self.assertEqual(ext["moduleSha256"], hashlib.sha256(module.read_bytes()).hexdigest())
        self.assertTrue(ext["classInBundle"] and ext["styleCss"])

    def test_feature_start_only_false_disables(self):
        # Kar.extract(): only the exact string "false" turns feature installation off
        self.assertFalse(kar_info.read_kar(build_kar(self.tmp / "a.kar", feature_start="false"))["featureStart"])
        self.assertTrue(kar_info.read_kar(build_kar(self.tmp / "b.kar", feature_start=None))["featureStart"])
        self.assertTrue(kar_info.read_kar(build_kar(self.tmp / "c.kar", feature_start="FALSE"))["featureStart"])

    def test_conflicts_ignore_same_file_name(self):
        a = kar_info.read_kar(build_kar(self.tmp / "x.kar"))
        other_dir = self.tmp / "deploy"
        other_dir.mkdir()
        same = kar_info.read_kar(build_kar(other_dir / "x.kar"))
        renamed = kar_info.read_kar(build_kar(other_dir / "x-1.0.1.kar"))
        unrelated = kar_info.read_kar(build_kar(other_dir / "y.kar", plugin="icon-catalog"))
        found = kar_info.conflicts(a, [same, renamed, unrelated])
        self.assertEqual({what for _, what in found}, {"feature opennms-lab-node-inventory", "UI extension id labNodeInventory"})
        self.assertTrue(all(f.endswith("x-1.0.1.kar") for f, _ in found))

    def test_mvn_paths(self):
        self.assertEqual(kar_info.mvn_to_entry("mvn:org.a/b/1.0"), "repository/org/a/b/1.0/b-1.0.jar")
        self.assertEqual(kar_info.mvn_to_entry("wrap:mvn:org.a/b/1.0/xml/features"), "repository/org/a/b/1.0/b-1.0-features.xml")
        self.assertIsNone(kar_info.mvn_to_entry("file:/tmp/x.jar"))
        self.assertEqual(kar_info.entry_to_mvn("repository/org/a/b/1.0/b-1.0-features.xml"), "mvn:org.a/b/1.0/xml/features")

    def test_not_a_kar(self):
        bogus = self.tmp / "bogus.kar"
        bogus.write_text("hello")
        with self.assertRaises(kar_info.KarError):
            kar_info.read_kar(bogus)


class CheckKarTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        check_plugins.results.clear()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def levels(self):
        return [r[0] for r in check_plugins.results]

    def test_demo_kars_pass(self):
        seen: dict[str, str] = {}
        for plugin in ("node-inventory", "icon-catalog"):
            check_plugins.check_kar(build_kar(self.tmp / f"{plugin}.kar", plugin=plugin), seen)
        self.assertNotIn("FAIL", self.levels())
        self.assertNotIn("WARN", self.levels())

    def test_module_without_window_assignment_fails(self):
        kar = build_kar(self.tmp / "broken.kar", module_edit=lambda b: b.replace(b"window", b"globalThis_"))
        check_plugins.check_kar(kar, {})
        self.assertTrue(any(r[0] == "FAIL" and "never assigns" in r[2] for r in check_plugins.results))

    def test_feature_start_false_warns(self):
        check_plugins.check_kar(build_kar(self.tmp / "fs.kar", feature_start="false"), {})
        self.assertTrue(any(r[0] == "WARN" and "Karaf-Feature-Start" in r[2] for r in check_plugins.results))


class LibShTest(unittest.TestCase):
    """scripts/lib.sh reads .env like compose: the environment wins, quotes are stripped."""

    def run_lib(self, env_text: str, extra_env: dict[str, str], expr: str) -> str:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "scripts").mkdir()
            shutil.copy(REPO / "scripts/lib.sh", Path(d) / "scripts/lib.sh")
            (Path(d) / ".env").write_text(env_text, encoding="utf-8")
            env = {k: v for k, v in os.environ.items() if not k.startswith(("ONMS_", "CONTAINER_ENGINE"))}
            env.update(extra_env)
            out = subprocess.run(["bash", "-c", f'. scripts/lib.sh; {expr}'], cwd=d, env=env,
                                 capture_output=True, text=True, check=True)
            return out.stdout.strip()

    def test_env_file(self):
        env = 'ONMS_HTTP_PORT=18980\r\nONMS_USER="lab"\n# comment\nexport ONMS_PASS=\'a b\'\nJAVA_OPTS=-Xms1g -Xmx2g  \n'
        self.assertEqual(self.run_lib(env, {}, 'echo "$ONMS_URL|$ONMS_USER|$ONMS_PASS|$JAVA_OPTS"'),
                         "http://localhost:18980|lab|a b|-Xms1g -Xmx2g")

    def test_environment_wins(self):
        self.assertEqual(self.run_lib("ONMS_PASS=fromfile\n", {"ONMS_PASS": "fromenv"}, 'echo "$ONMS_PASS"'), "fromenv")

    def test_bind_address_becomes_url(self):
        self.assertEqual(self.run_lib("ONMS_HTTP_BIND=192.0.2.10\n", {}, 'echo "$ONMS_URL"'), "http://192.0.2.10:8980")
        self.assertEqual(self.run_lib("ONMS_HTTP_BIND=0.0.0.0\n", {}, 'echo "$ONMS_URL"'), "http://localhost:8980")
        self.assertEqual(self.run_lib("", {"ONMS_URL": "http://nms:8980/"}, 'echo "$ONMS_URL"'), "http://nms:8980")


if __name__ == "__main__":
    unittest.main()
