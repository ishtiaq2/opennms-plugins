# OpenNMS architecture, step by step

This guide explains how OpenNMS Horizon 33.1.8 is built inside, using the lab in this repository as
the running example. It starts from the outside (a container with one Java process), opens up each
layer in turn (the daemons, the Jetty web server, the web application, Karaf and Felix, bundles and
plugins), and then follows things as they move through those layers: a plugin being deployed, a
service being looked up, a request finding its way to a plugin's JAR, a page loading end to end.

Every step has a diagram. The diagrams are drawn to the same colour code, so a Karaf part is always
purple and a Jetty part always orange, and every statement in the text was checked against the
OpenNMS 33.1.8 source (see [how this guide was checked](#how-this-guide-was-checked)).

![The big picture](images/01-big-picture.svg)

## The steps

| Step | Diagram | What it explains |
|---|---|---|
| [1. The big picture](01-the-big-picture.md) | everything at once | the parts, where they run, and which step explains each |
| [2. One process](02-one-process.md) | container start to JVM | what the container runs, and how one JVM loads OpenNMS |
| [3. The daemons](03-daemons.md) | service list, Spring contexts | how OpenNMS starts its services, in which order, and how they share beans |
| [4. Jetty](04-jetty.md) | server, handlers, web apps | the web server inside the process: port, handlers, web applications |
| [5. The web application](05-the-web-application.md) | listeners, filters, servlets | what happens inside `/opennms` for every request |
| [6. Karaf](06-karaf.md) | Karaf's start-up | how the web application starts Karaf, and what Karaf does at boot |
| [7. Felix](07-felix.md) | the OSGi framework | the engine under Karaf: bundles, life cycle, services, the system bundle |
| [8. JARs, bundles, features, KARs](08-jars-bundles-features-kars.md) | a plugin opened up | what a plugin is made of, and where each kind of file lives |
| [9. Class loaders and threads](09-class-loaders-and-threads.md) | loaders, one call stack | why a plugin is not a process, and what it is instead |
| [10. Deploying a plugin](10-deploying-a-plugin.md) | sequence | from a file in `./deploy` to a menu entry, step by step |
| [11. Services and the bridge](11-services-and-the-bridge.md) | two registries | how the parts find each other at run time |
| [12. Jetty and Felix](12-jetty-and-felix.md) | request routing | how a request gets from the network into OSGi, and back |
| [13. Plugin A and plugin B](13-plugin-uis.md) | URL map | how one server serves many separately packaged UIs |
| [14. Shared assets](14-shared-assets.md) | one folder, many readers | where the shared files are, and who finds them how |
| [15. One page load](15-one-page-load.md) | sequence | every request of one page, and which part answers it |
| [16. Around the core](16-around-the-core.md) | neighbours | database, events, configuration, logs, time series, security, Minion |

Read them in order the first time: Steps 1 to 9 build up the parts, Steps 10 to 15 put them in
motion, and Step 16 fills in what the lab does not open up. Each step begins with a short answer,
then walks through its diagram (the blue numbers in the diagram are the numbers of the paragraphs),
then shows how to see the same thing in the running lab, and ends with the points to remember.

## Your questions, and where they are answered

| Question | Answer in short | Steps |
|---|---|---|
| Is OpenNMS a process, running in a JVM? How is it loaded? | Yes: one Java process, PID 1 in the container. A small launcher JAR builds a class loader over `lib/` and calls the OpenNMS controller, which starts the services listed in `etc/service-configuration.xml`. | [2](02-one-process.md), [3](03-daemons.md) |
| What is Karaf? | An OSGi container (features, KARs, deployers, shell, configuration, logging), started inside OpenNMS by a listener of the web application, with `$OPENNMS_HOME` as its home. | [6](06-karaf.md) |
| What is Felix? | The OSGi framework under Karaf: it loads bundles with class loaders of their own, runs their life cycle and keeps the service registry. Several Felix sub-projects (FileInstall, ConfigAdmin, the HTTP bridge) run as bundles. | [7](07-felix.md) |
| What is Jetty? | The web server inside the same process, built and started by the `JettyServer` daemon, listening on port 8980 and hosting the web applications in `jetty-webapps/`. | [4](04-jetty.md), [5](05-the-web-application.md) |
| Plugins, bundles and JARs? | A JAR is a ZIP of classes; a bundle is a JAR with OSGi headers; a feature is a named set of bundles; a KAR packs features and bundles into one file; a plugin is usually a KAR whose bundle registers Integration API services. | [8](08-jars-bundles-features-kars.md) |
| Is each plugin or bundle a separate process? | No. Every bundle is a class loader plus objects inside the one JVM; a request runs from Jetty to a plugin's code on one thread, in one call stack. | [9](09-class-loaders-and-threads.md) |
| What happens when a plugin is deployed? How does OpenNMS find and load it? | A FileInstall watcher sees the KAR, Karaf unpacks it and installs its feature, Felix installs, wires and starts the bundle, Blueprint registers its `UIExtension` service, and the api-layer's registry picks it up. | [10](10-deploying-a-plugin.md) |
| Shared assets: how do plugins and other parts find them? | They are plain files inside the `/opennms` web application (a host folder mounted there), served by Jetty's `DefaultServlet` at `/opennms/assets/shared/`. Plugins' JavaScript finds them through that fixed URL and `manifest.json`; no Java code is involved. | [14](14-shared-assets.md) |
| How do the parts interact? | Through two service registries joined by a bridge, a class space shared through the system bundle, the event bus, the database, and HTTP inside one Jetty. | [11](11-services-and-the-bridge.md), [15](15-one-page-load.md) |
| How does Jetty interact with the inside and the outside, for example with Felix and a user? | Users only reach Jetty's port. The web application's last filter, the `ProxyFilter`, hands paths that OSGi claimed to the Felix HTTP bridge, which runs OSGi servlets on the same Jetty thread. | [4](04-jetty.md), [5](05-the-web-application.md), [12](12-jetty-and-felix.md) |
| How does one server serve plugin A's UI and plugin B's UI? | Both come through the same REST endpoint; the extension id in the URL selects the bundle, and the file is read from that bundle's JAR. The routes that show them live in the browser. | [13](13-plugin-uis.md) |
| What else is there? | Spring contexts, the event bus, PostgreSQL, configuration files, logs, time series, security, Minion and Sentinel. | [3](03-daemons.md), [16](16-around-the-core.md) |

## Trying things in the lab

The "see it in the lab" sections assume the lab from [Part 0](../00-install-opennms-and-postgresql.md)
is running, with both plugins deployed as in [Part 6](../06-installing-the-plugins.md). Commands are
written for Podman; with Docker, replace `podman` by `docker`. Commands that start with
`scripts/karaf.sh` run one command in Karaf's shell (over SSH, as the web UI's admin user). The
expected output is described rather than pasted, because it depends on your machine; where a
count or a name is certain from the source, the text says so.

## Words used in this guide

| Word | Meaning here |
|---|---|
| JVM | the Java virtual machine: one operating-system process that runs Java code |
| class loader | the object that finds and defines classes for the JVM, from a list of JARs and folders; every class is identified by its name **and** its loader |
| daemon | an OpenNMS service such as Pollerd or Eventd, started from `etc/service-configuration.xml` |
| MBean | a Java object registered in JMX, the JVM's management registry; each daemon is one |
| Spring context | a container of objects (beans) built from XML files; a child context sees its parent's beans |
| web application | a folder of servlets, filters, pages and files that Jetty serves under one context path, here `/opennms` |
| servlet, filter | the Java web API: a servlet answers requests, filters run before it, in order |
| bundle | a JAR with OSGi headers, loaded by Felix with a class loader of its own |
| feature | a named set of bundles, other features and configuration, defined in a features XML |
| KAR | Karaf ARchive: one ZIP file with a features XML and every bundle it needs |
| OSGi service | an object a bundle registers under an interface name, with properties, for other bundles to find |
| Blueprint | an XML way (Apache Aries) to create objects in a bundle and register or reference services |
| whiteboard | a pattern: register a service with the right properties and someone else picks it up (servlets, JAX-RS resources, UI extensions) |
| start level | a number that orders bundle start-up; Felix raises the level step by step at boot |
| OIA | the OpenNMS Integration API, the stable interfaces plugins compile against |

## How the diagrams are made

The pictures in [`images/`](images/) are SVG files generated by
[`images/make_diagrams.py`](images/make_diagrams.py), a Python script without dependencies. To change
a diagram, edit the script and run it:

```bash
python3 docs/architecture/images/make_diagrams.py          # rewrite every SVG
python3 docs/architecture/images/make_diagrams.py --check  # fail if an SVG is out of date
```

`scripts/validate-repo.sh` runs the check, so the pictures and the script cannot drift apart.

## How this guide was checked

Every statement about OpenNMS, Jetty, Karaf and Felix was checked in the source code of the exact
versions the Horizon 33.1.8 image ships: OpenNMS `opennms-33.1.8-1`, Jetty `9.4.57.v20241219`, Karaf
`4.3.10`, Felix framework `6.0.5` and Felix FileInstall `3.7.4`. The
[source trace](../reference/source-trace.md#architecture-guide-process-and-daemons) links each one to
its file and line. What could not be done where this guide was written is run the real OpenNMS
container; the lab sections tell you what to look for, and [verification](../reference/verification.md)
lists what was tested and how.
