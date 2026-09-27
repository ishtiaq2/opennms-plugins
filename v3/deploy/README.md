# deploy

Karaf watches this folder while OpenNMS runs. It is bind-mounted read-only into the Horizon
container at `/opt/opennms-lab-deploy`, and `etc-overlay/org.apache.felix.fileinstall-lab.cfg`
turns that directory into a second Karaf deploy folder.

| You do | Karaf does, within about a second |
|---|---|
| put a `.kar` file here | installs the KAR and, unless its manifest says `Karaf-Feature-Start: false`, its features |
| replace the file with a new build | uninstalls the old KAR and installs the new one |
| delete the file | uninstalls the KAR and its features |

Use the scripts rather than a plain `cp`, because they copy under a temporary name and rename, so
Karaf never reads a half-written file, and they wait until OpenNMS lists the plugin:

```bash
scripts/deploy-plugin.sh node-inventory        # a demo plugin, after scripts/build-plugins.sh
scripts/deploy-plugin.sh ~/src/my-plugin/assembly/kar/target/my-plugin.kar
scripts/undeploy-plugin.sh node-inventory
```

Karaf names a KAR after its file name without `.kar`, so keep one stable file name per plugin
(no version number in it). Two files with different names but the same features would both be
installed. Only `*.kar` files are picked up; this README is ignored. `.gitignore` keeps built KARs
out of Git.
