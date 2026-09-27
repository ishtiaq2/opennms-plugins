#!/usr/bin/env python3
"""Draws the diagrams of docs/architecture/ as SVG files (standard library only).

    python3 docs/architecture/images/make_diagrams.py            # writes all *.svg next to this file
    python3 docs/architecture/images/make_diagrams.py --check    # exit 1 if a committed SVG is out of date

Black circles in the big picture give the step of the guide that explains a part; blue circles in
the other diagrams give the order of events that the step's text walks through.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svglib import ARROW, Svg, text_width  # noqa: E402

OUT = Path(__file__).resolve().parent
DIAGRAMS = {}


def diagram(name):
    def reg(fn):
        DIAGRAMS[name] = fn
        return fn
    return reg


def chips(s: Svg, x, y, names, style="daemon", h=30, gap=8, size=13, pad=12):
    """A row of small boxes; returns the x after the last one."""
    for n in names:
        st = style
        if isinstance(n, tuple):
            n, st = n
        w = round(text_width(n, size) + 2 * pad)
        s.box(x, y, w, h, st, lines=[n], size=size, center=True, rx=7)
        x += w + gap
    return x


def down(s: Svg, x, y1, y2, kind="default", **kw):
    s.arrow([(x, y1), (x, y2)], kind, **kw)


# ------------------------------------------------------------------------------------------------
@diagram("01-big-picture")
def big_picture():
    s = Svg(1200, 1032, "OpenNMS Horizon 33.1.8 in this lab: the big picture",
            "One Java process runs the daemons, Jetty with the web application, and Karaf/Felix with every "
            "bundle and plugin.\nA black circle gives the step of this guide that explains the part.")
    s.legend(24, 114, [("host", "your machine"), ("container", "container"), ("daemon", "OpenNMS daemons"),
                       ("jetty", "Jetty / web app"), ("karaf", "Karaf / Felix (OSGi)"), ("plugin", "plugins"),
                       ("assets", "shared assets"), ("data", "data, configuration")])

    # host column ---------------------------------------------------------------------------------
    s.group(16, 128, 200, 888, "host", "Your machine")
    s.box(30, 164, 172, 86, "white", "Browser", ["`/opennms/`", "`/opennms/ui/`"])
    s.box(30, 266, 172, 58, "host", "`.env`", ["passwords, ports"])
    s.box(30, 592, 172, 92, "assets", "`./shared-assets/`", ["icons, images,", "`manifest.json`",
                                                             "(mounted read-only)"])
    s.box(30, 800, 172, 88, "karaf", "`./etc-overlay/`", ["copied into `etc/`", "at every start"])
    s.box(30, 904, 172, 90, "plugin", "`./deploy/`", ["plugin KARs,", "mounted read-only"])

    # container and JVM ---------------------------------------------------------------------------
    s.group(232, 128, 716, 888, "container", "Container onms-shared-assets-horizon (opennms/horizon:33.1.8)",
            dash="7 5")
    s.group(248, 164, 684, 844, "jvm", "One JVM, PID 1: java ... -jar lib/opennms_bootstrap.jar start",
            sw=2.6, badge=2)

    # daemons
    s.group(264, 204, 652, 136, "daemon", "OpenNMS daemons, started from etc/service-configuration.xml",
            badge=3)
    chips(s, 280, 240, ["Eventd", "Alarmd", "Pollerd", "Provisiond", "+ 22 more", ("JettyServer", "jetty")])
    s.box(280, 282, 330, 46, "white", lines=["Spring contexts: DAOs, `dataSource`"])
    s.box(620, 282, 280, 46, "white", lines=["OpenNMS service registry"])

    # jetty + webapp
    s.group(264, 356, 652, 350, "jetty", "Jetty 9.4.57, started by the JettyServer daemon: port 8980", badge=4)
    s.box(280, 396, 140, 84, "jetty", "ROOT: `/`", ["redirects to", "`/opennms/`"])
    s.group(432, 392, 468, 300, "webapp", "/opennms web application", badge=5)
    s.box(446, 428, 440, 32, "white", lines=["Filters: headers, Spring Security, ..., ProxyFilter"], center=True)
    s.box(446, 472, 150, 206, "jetty", "DefaultServlet", ["static files:", "the Vue UI `ui/`,", "`assets/`, ..."])
    s.box(458, 590, 126, 76, "assets", lines=["`assets/shared/`", "your folder,", "read-only"], center=True,
          size=12.5, badge=14)
    s.box(604, 472, 138, 96, "jetty", "Classic UI", ["JSP pages,", "Spring MVC", "`*.jsp`, `*.htm`"])
    s.box(750, 472, 136, 96, "jetty", "Apache CXF", ["REST API", "`/rest/*`", "`/api/v2/*`"])
    s.box(604, 580, 138, 98, "white", "Spring (web)", ["parent context:", "the daemons'", "`webContext`"])
    s.box(750, 580, 136, 98, "karaf", "ProxyFilter", ["paths claimed", "by OSGi go", "to Felix"], badge=12)

    # karaf
    s.group(264, 722, 652, 272, "karaf", "Karaf 4.3.10 on Felix 6.0.5 (OSGi), started by the web app", badge=6)
    s.box(280, 762, 206, 70, "bundle", "Felix framework", ["bundles, class loaders,", "service registry"],
          badge=7)
    s.box(494, 762, 206, 70, "bundle", "Karaf services", ["features, KARs, config,", "logging, SSH shell"])
    s.box(708, 762, 192, 70, "bundle", "Felix HTTP bridge", ["servlets and JAX-RS", "inside Jetty"], badge=12)
    s.box(280, 842, 206, 70, "bundle", "api-layer", ["implements the", "Integration API (OIA)"])
    s.box(494, 842, 206, 70, "bundle", "ui-extension", ["`/rest/plugins`: lists", "and serves UI modules"],
          badge=13)
    s.box(708, 842, 192, 70, "bundle", "OnmsOSGiBridge", ["mirrors the two", "service registries"], badge=11)
    s.box(280, 922, 266, 58, "white", "Deploy watchers", ["`deploy/`, `/opt/opennms-lab-deploy/`"], badge=10)
    s.box(554, 922, 170, 58, "plugin", "Node Inventory", ["plugin bundle (A)"], badge=8)
    s.box(732, 922, 168, 58, "plugin", "Icon Catalog", ["plugin bundle (B)"])

    # database and storage --------------------------------------------------------------------------
    s.group(964, 128, 220, 200, "container", "Database container", dash="7 5")
    s.box(980, 166, 188, 146, "data", "PostgreSQL 15", ["`database:5432`", "volume `pgdata`",
                                                        "inventory, events,", "alarms, ..."], badge=16)
    s.group(964, 344, 220, 452, "host", "Storage")
    s.box(980, 382, 188, 76, "data", "`etc/`", ["volume `onms-etc`", "all configuration"])
    s.box(980, 470, 188, 76, "data", "`/opennms-data/`", ["volume `onms-data`", "RRD files, reports"])
    s.box(980, 558, 188, 94, "data", "`system/`", ["in the image:", "bundles and features", "(Maven layout)"])
    s.box(980, 664, 188, 116, "data", "`data/`, `logs/`", ["inside the container:", "Karaf caches,", "log files"])
    s.box(964, 812, 220, 80, "note", "Published ports", ["`8980` web, `8101` SSH", "on `127.0.0.1`"])

    # arrows ----------------------------------------------------------------------------------------
    s.arrow([(202, 207), (240, 207), (240, 438), (262, 438)], "http", "HTTP", lx=221, ly=199)
    s.arrow([(202, 640), (456, 640)], "assets", dash="6 4")
    s.arrow([(202, 844), (240, 844), (240, 936), (278, 936)], "osgi", dash="6 4")
    s.arrow([(202, 958), (278, 958)], "plugin", dash="6 4")
    s.arrow([(916, 255), (978, 255)], "data", "JDBC", lx=946, ly=247)
    s.arrow([(818, 678), (818, 760)], "osgi", "OSGi paths", lx=812, ly=719, label_anchor="end")
    s.arrow([(900, 877), (924, 877), (924, 305), (902, 305)], "osgi", start=True)
    return s


# ------------------------------------------------------------------------------------------------
@diagram("02-one-process")
def one_process():
    s = Svg(1100, 736, "From container start to one Java process",
            "What /entrypoint.sh -s runs, and how lib/opennms_bootstrap.jar becomes the running OpenNMS.\n"
            "Blue circles give the order of events; dashed boxes are short-lived processes that exit.")
    t = s.top() + 18
    s.group(24, t, 500, 520, "container", "In the container: /entrypoint.sh -s, as uid 10001", dash="7 5")
    x, w = 44, 460
    s.box(x, t + 44, w, 88, "grey", "Prepare etc/", ["empty volume? copy `etc-pristine/` into it,",
                                                     "fill confd templates, then copy the overlays",
                                                     "(the lab's `etc-overlay/` goes into `etc/`)"], seq=1)
    s.box(x, t + 152, w, 106, "white", "Config tester, a short Java process",
          ["`java -Dopennms.manager.class=...ConfigTester`", "`     -jar lib/opennms_bootstrap.jar -a`",
           "checks the configuration files, then exits;", "an error stops the container here"],
          dash="6 4", seq=2)
    s.box(x, t + 278, w, 106, "white", "Installer, only when etc/configured is missing",
          ["`java -cp lib/opennms_bootstrap.jar`", "`     org.opennms.bootstrap.InstallerBootstrap`",
           "creates or upgrades the database schema,", "writes `etc/configured`, then exits"],
          dash="6 4", seq=3)
    s.box(x, t + 404, w, 96, "jvm", "The long-running process",
          ["`exec java ... -jar lib/opennms_bootstrap.jar start`", "`exec`: the shell replaces itself with Java, which",
           "is now PID 1 and runs until the container stops."], sw=2.4, seq=4)
    for y1, y2 in ((t + 132, t + 150), (t + 258, t + 276), (t + 384, t + 402)):
        down(s, 274, y1, y2)

    s.group(548, t, 528, 520, "jvm", "Inside the JVM", sw=2.4)
    x, w = 568, 488
    s.box(x, t + 44, w, 160, "white", "Bootstrap.main()",
          ["finds `opennms.home` and reads these files into system", "properties (a `-D` option wins over a file):",
           "`jetty-webapps/opennms/WEB-INF/version.properties`,", "`etc/bootstrap.properties`,",
           "`etc/rrd-configuration.properties`, `etc/libraries.properties`,",
           "`etc/opennms.properties`, `etc/opennms.properties.d/*.properties`"], seq=5)
    s.box(x, t + 222, w, 72, "white", "Builds the lib/ class loader",
          ["a `URLClassLoader` over `lib/endorsed/`, `classes/`, every", "`lib/*.jar` and `etc/`: all of OpenNMS's code"],
          seq=6)
    s.box(x, t + 312, w, 90, "white", "Starts a thread named \"Main\"",
          ["loads `Controller` through that class loader and calls its", "`main(\"start\")` on the new thread; "
           "`logs/opennms.pid` gets", "the PID (the config tester reuses this launcher)"], seq=7)
    s.box(x, t + 420, w, 80, "daemon", "Controller > Starter > Invoker",
          ["logs to `logs/manager.log` and starts the services listed in", "`etc/service-configuration.xml` (Step 3)"],
          seq=8)
    for y1, y2 in ((t + 204, t + 220), (t + 294, t + 310), (t + 402, t + 418)):
        down(s, 812, y1, y2)
    s.arrow([(504, t + 452), (536, t + 452), (536, t + 124), (566, t + 124)], "default")

    s.box(24, t + 540, 1052, 64, "note", lines=[
        "Everything after this point runs inside this one process: the daemons, Jetty, the web application, "
        "Karaf, Felix,", "every bundle and every plugin. They are objects and threads that share one heap and "
        "one PID, not processes of their own."])
    return s


# ------------------------------------------------------------------------------------------------
SERVICES = ["Manager", "TestLoadLibraries", "Eventd", "Alarmd", "Bsmd", "Ticketer", "Queued", "Actiond",
            "Notifd", "Scriptd", "Rtcd", "Pollerd", "EnhancedLinkd", "Collectd", "Discovery", "Vacuumd",
            "EventTranslator", "PassiveStatusd", "Statsd", "Provisiond", "Reportd", "Ackd", "JettyServer",
            "KarafStartupMonitor", "Telemetryd", "Trapd", "PerspectivePoller"]


@diagram("03-daemons")
def daemons():
    s = Svg(1100, 900, "The daemons: one list, two passes, one tree of Spring contexts",
            "The Invoker registers each enabled service of etc/service-configuration.xml as a JMX MBean, calls init() "
            "on all of them\nin file order (pass 0), then start() on all of them (pass 1). Most daemons keep their "
            "beans in a Spring context.")
    t = s.top() + 16
    # left: the service table
    s.group(24, t, 520, 762, "daemon", "etc/service-configuration.xml, the 27 enabled services")
    x0, y0, rh = 40, t + 64, 22
    c0, c1 = x0 + 214, x0 + 382
    s.text(x0 + 30, y0 - 12, "MBean OpenNMS:Name=...", size=12.5, weight="bold", color="#064e3b")
    s.text(c0, y0 - 12, "pass 0", size=12.5, weight="bold", color="#064e3b")
    s.text(c1, y0 - 12, "pass 1", size=12.5, weight="bold", color="#064e3b")
    for i, name in enumerate(SERVICES):
        y = y0 + i * rh
        style = {"JettyServer": ("#fff7ed", "#7c2d12"), "KarafStartupMonitor": ("#f5f3ff", "#4c1d95"),
                 "Eventd": ("#ecfdf5", "#064e3b")}.get(name)
        if style:
            s.rect(x0 - 6, y - 1, 474, rh - 2, style[0], style[0], rx=4, sw=0)
        col = style[1] if style else "#0f172a"
        s.text(x0 + 16, y + 15, str(i + 1), size=12, anchor="end", color="#64748b")
        s.text(x0 + 30, y + 15, name, size=13, color=col, weight="bold" if style else "normal")
        p0 = "doTestLoadLibraries()" if name == "TestLoadLibraries" else "init()"
        s.text(c0, y + 15, p0, size=12.5, color=col)
        if name not in ("Manager", "TestLoadLibraries"):
            s.text(c1, y + 15, "start()", size=12.5, color=col)
    yb = y0 + len(SERVICES) * rh
    s.arrow([(c0 - 12, y0 + 18), (c0 - 12, yb - 2)], "daemon", sw=2)
    s.arrow([(c1 - 12, y0 + 18), (c1 - 12, yb - 2)], "daemon", sw=2)
    s.seq(c0 - 12, y0 + 6, 1)
    s.seq(c1 - 12, y0 + 6, 2)
    s.box(40, yb + 20, 488, 76, "note", lines=[
        "Disabled in 33.1.8: Correlator, SnmpPoller, Tl1d, Syslogd,", "AsteriskGateway. A service that "
        "throws in init() or start()", "stops OpenNMS (\"Shutting down and exiting\")."], size=12.5)
    # callouts for the two services that matter for the web and OSGi
    s.box(566, t + 4, 510, 104, "jetty", "JettyServer (row 23)",
          ["init(): builds the Jetty server from `etc/jetty.xml` or the", "built-in copy. start(): starts Jetty, which "
           "deploys the web", "apps, and the /opennms app starts Karaf (Steps 4 to 6)."], seq=3)
    s.box(566, t + 120, 510, 88, "karaf", "KarafStartupMonitor (row 24)",
          ["start() checks every 5 s until Karaf's last boot feature has", "registered its health service; after "
           "about 5 minutes", "without it, OpenNMS stops."], seq=4)
    # right: the Spring context tree
    g = t + 226
    s.group(566, g, 510, 536, "white", "Spring contexts: a tree inside the JVM")
    nodes = [  # (level, row, text, style)
        (0, 0, "soaContext: the OpenNMS service registry", "white"),
        (1, 1, "commonContext: shared configuration", "white"),
        (2, 2, "daemonContext", "white"),
        (3, 3, "daoContext: `dataSource`, Hibernate, DAOs", "data"),
        (4, 4, "eventDaemonContext (Eventd)", "daemon"),
        (4, 5, "alarmdContext (Alarmd), queued, rtc, ...", "daemon"),
        (4, 6, "pollerConfigContext", "white"),
        (5, 7, "notifdContext (Notifd)", "daemon"),
        (5, 8, "thresholdingContext", "white"),
        (6, 9, "pollerdContext, collectdContext", "daemon"),
        (6, 10, "webContext", "jetty"),
    ]
    bx, by, bh = 584, g + 44, 26
    pos = {}
    for lvl, row, txt, st in nodes:
        x = bx + lvl * 26
        y = by + row * (bh + 10)
        w = round(text_width(txt, 12.5) + 26)
        s.box(x, y, w, bh, st, lines=[txt], size=12.5, rx=6)
        pos[row] = (x, y)
    parents = {1: 0, 2: 1, 3: 2, 4: 3, 5: 3, 6: 3, 7: 6, 8: 6, 9: 8, 10: 8}
    for child, par in parents.items():
        px, py = pos[par]
        cx, cy = pos[child]
        s.arrow([(px + 12, py + bh), (px + 12, cy + bh / 2), (cx - 2, cy + bh / 2)], "grey", sw=1.3, end=False)
    wx, wy = pos[10]
    s.arrow([(wx + 118, wy + bh / 2), (wx + 150, wy + bh / 2)], "http", sw=1.5)
    s.text(wx + 156, wy + 12, "parent of the /opennms", size=12, color="#7c2d12")
    s.text(wx + 156, wy + 27, "web app's context (Step 5)", size=12, color="#7c2d12")
    s.box(584, g + 488 - 30, 474, 62, "note", lines=["A child context sees every bean of its parents: the web "
                                                    "app", "uses the daemons' DAOs and the same database pool."],
          size=12.5)
    return s



# ------------------------------------------------------------------------------------------------
@diagram("04-jetty")
def jetty():
    s = Svg(1100, 770, "Jetty inside OpenNMS: one server, one port, several web applications",
            "The JettyServer daemon builds the server from jetty.xml in pass 0 and starts it in pass 1. Every "
            "request runs\nthrough the handlers below on one of Jetty's threads; the ContextHandlerCollection picks "
            "the web application.")
    t = s.top() + 18
    s.box(24, t + 44, 180, 90, "white", "Clients", ["browsers, curl,", "the lab's scripts"])
    s.box(24, t + 300, 196, 132, "grey", "Not through Jetty", ["own listeners, in the", "same process:",
                                                           "Karaf SSH `8101`,", "SNMP traps `1162/udp`"])
    s.group(240, t, 540, 628, "jetty", "Jetty 9.4.57, built from jetty.xml by JettyServer")
    s.box(260, t + 44, 500, 70, "white", "ServerConnector: HTTP/1.1 on 0.0.0.0:8980",
          ["port from `org.opennms.netmgt.jetty.port`; HTTPS (8443) and", "AJP (8981) are in the file, commented out"],
          seq=1)
    s.box(260, t + 128, 500, 52, "white", "Thread pool", ["a `qtp<id>-<n>` thread runs the request from here on"],
          seq=2)
    s.box(260, t + 194, 500, 52, "white", "MDCHandler (OpenNMS)",
          ["log prefix `web`: what the request logs goes to `logs/web.log`"], seq=3)
    s.group(260, t + 262, 500, 346, "white", "HandlerCollection: calls each handler in turn", label_size=13.5)
    s.box(278, t + 300, 464, 84, "jetty", "RewriteHandler: response headers",
          ["`X-Frame-Options: SAMEORIGIN` on everything;", "`Cache-Control: no-store` on `/opennms/...`",
           "except under `/opennms/assets/`"], seq=4)
    s.box(278, t + 398, 464, 134, "jetty", "ContextHandlerCollection: which web app?",
          ["the longest context path that matches the URL"], seq=5)
    for i, (path, sub) in enumerate((("`/`", "ROOT"), ("`/opennms`", "opennms"), ("`/hawtio`", "if installed"))):
        s.box(294 + i * 148, t + 462, 136, 54, "webapp", lines=[path, sub], center=True)
    s.box(278, t + 546, 464, 50, "jetty", "DefaultHandler", ["404 when no web application handled it"], seq=6)
    for y1, y2 in ((t + 114, t + 126), (t + 180, t + 192), (t + 246, t + 260)):
        down(s, 510, y1, y2, "http")
    s.arrow([(204, t + 89), (258, t + 89)], "http", "HTTP", lx=230, ly=t + 81)

    s.group(800, t, 276, 628, "white", "Where the web apps come from")
    s.box(816, t + 44, 244, 124, "white", "DeploymentManager",
          ["with `OpenNMSWebAppProvider`:", "scans `jetty-webapps/` every", "10 s; each directory there",
           "becomes a web application"])
    s.box(816, t + 184, 244, 136, "data", "`jetty-webapps/`",
          ["`ROOT/     -> /`", "`opennms/  -> /opennms`", "`hawtio/   -> /hawtio`", "(if installed)"])
    s.box(816, t + 336, 244, 104, "white", "Configuration", ["`etc/jetty.xml` if it exists,",
                                                          "else the copy built into", "OpenNMS (a sample is",
                                                          "`etc/examples/jetty.xml`)"])
    s.box(816, t + 456, 244, 76, "white", "JMX", ["Jetty's MBeans join the", "platform MBean server"])
    s.arrow([(816, t + 262), (792, t + 262), (792, t + 489), (744, t + 489)], "http", dash="6 4")
    s.label(792, t + 380, "deploys", color=ARROW["http"])
    return s


# ------------------------------------------------------------------------------------------------
FILTERS = [
    ("Security headers (5 filters)", "`/*`", "CSP, nosniff, Referrer-Policy, HSTS, Permissions-Policy"),
    ("characterEncodingFilter", "`/*`", "UTF-8 for requests and responses"),
    ("openSessionInViewFilter", "`/*`", "one Hibernate session for the whole request"),
    ("Origin Filter", "`/rest/*`, `/nrt/*`", "checks the Origin header"),
    ("springSecurityFilterChain", "`/*`", "login and roles; `/assets/**` needs no login"),
    ("StoreRequestProperties, ...", "various", "user settings, refresh headers, table export"),
    ("SpaRouting", "`/ui`, `/ui/*`", "deep links of the Vue UI get `ui/index.html`"),
    ("httpsRewriteFilter", "`/`, `/frontPage.jsp`", "front-page redirects"),
]
SERVLETS = [
    ("`/rest/*`", "cxfRestServlet: Apache CXF, REST API v1"),
    ("`/api/v2/*`", "cxfRest2Servlet: Apache CXF, REST API v2"),
    ("`*.htm` and 23 more paths", "Spring `DispatcherServlet`: MVC controllers"),
    ("`*.jsp`", "the JSP servlet (Jasper) from Jetty's defaults"),
    ("about 45 more paths", "form handlers, e.g. `/admin/deleteNodes`"),
    ("`/`: everything else", "`DefaultServlet`: files under `jetty-webapps/opennms/`"),
]


@diagram("05-webapp")
def webapp():
    s = Svg(1100, 900, "Inside the /opennms web application: listeners, filters, servlets",
            "At start-up the listeners run once. Then every request runs through the filters in order, and "
            "one servlet answers.\nThe ProxyFilter comes last: it hands paths that OSGi has claimed to Felix "
            "instead (Step 12).")
    t = s.top() + 18
    s.group(24, t, 1052, 112, "webapp", "At start-up, once: the listeners, in web.xml order")
    lst = [("Web UI set-up", ["`InitializerServletContextListener`", "users, groups, views"]),
           ("Spring root context", ["`ContextLoaderListener`", "parent: the daemons' `webContext`"]),
           ("WebAppListener", ["from `container/servlet`", "starts Karaf (Step 6)"]),
           ("ProxyListener", ["from the Felix HTTP proxy", "session events to Felix"])]
    for i, (ti, li) in enumerate(lst):
        s.box(40 + i * 257, t + 38, 247, 62, "white", ti, li, size=12, title_size=13.5, seq=i + 1)
    top = t + 128
    s.group(24, top, 540, 576, "webapp", "For every request: the filters, in order")
    for i, (name, pat, desc) in enumerate(FILTERS):
        y = top + 40 + i * 58
        s.box(40, y, 508, 50, "white", name, [desc], title_size=13.5, size=12.5)
        s.text(536, y + 21, pat, size=12.5, anchor="end", color="#7c2d12")
        if i:
            down(s, 294, y - 8, y - 1, "http", sw=1.4)
    y = top + 40 + len(FILTERS) * 58
    down(s, 294, y - 8, y - 1, "http", sw=1.4)
    s.box(40, y, 508, 50, "karaf", "ProxyFilter (merged from container/servlet)",
          ["path claimed in OSGi? then Felix, else continue"], title_size=13.5, size=12.5)
    s.text(536, y + 21, "`/*`", size=12.5, anchor="end", color="#4c1d95")

    s.group(584, top, 492, 576, "jetty", "... then one servlet, chosen by the URL")
    for i, (pat, desc) in enumerate(SERVLETS):
        yy = top + 40 + i * 88
        s.box(600, yy, 460, 76, "white", pat, [desc], title_size=13.5, size=12.5)
    s.arrow([(548, y + 25), (572, y + 25), (572, top + 56), (598, top + 56)], "http")
    s.box(24, top + 596, 540, 60, "karaf", "Felix HTTP bridge (Step 12)",
          ["OSGi servlets and JAX-RS resources, e.g. `/rest/plugins`"], size=12.5)
    s.box(584, top + 596, 492, 60, "note", lines=["Not claimed by OSGi: the request goes on to the servlet",
                                                  "whose mapping matches its URL (orange arrow)."], size=12.5)
    s.arrow([(294, y + 50), (294, top + 594)], "osgi", "claimed", lx=330, ly=top + 586)
    return s


# ------------------------------------------------------------------------------------------------
@diagram("06-karaf")
def karaf():
    s = Svg(1100, 900, "How Karaf starts inside the web application",
            "WebAppListener launches Karaf's Main with OPENNMS_HOME as Karaf's home. Karaf starts Felix, installs "
            "the startup\nbundles and raises the start level; FileInstall and the features service then do the "
            "rest in the background.")
    t = s.top() + 18
    s.group(24, t, 620, 760, "karaf", "Start-up, in order")
    x, w = 40, 588
    s.box(x, t + 40, w, 106, "white", "WebAppListener.contextInitialized()",
          ["runs on the thread `Main` while Jetty deploys `/opennms`; sets", "`karaf.home` = `karaf.base` = "
           "`/usr/share/opennms`, `karaf.etc` = `etc/`,", "`karaf.data` = `data/`, `karaf.log` = `logs/`; remote "
           "shell on,", "local console off, no lock file"], seq=1)
    s.box(x, t + 160, w, 106, "white", "new Main(...).launch()  (org.apache.karaf.main)",
          ["reads `etc/config.properties`, `etc/custom.properties`, ...;", "finds the Felix framework JAR in "
           "`system/`; builds a class", "loader for it; `framework.init()` and `framework.start()`;",
           "then returns: the rest happens on Felix's threads"], seq=2)
    s.box(x, t + 280, w, 70, "white", "First start only: the startup bundles",
          ["bundle cache empty? install the bundles of `etc/startup.properties`,", "each with its start level"],
          seq=3)
    s.box(x, t + 364, w, 118, "white", "The start level rises to 100 (thread FelixStartLevel)",
          ["bundles start level by level:"], seq=4)
    chips(s, x + 14, t + 426, ["5 Pax URL", "8 Pax Logging", "10 ConfigAdmin", "12 FileInstall",
                               "15 features"], style="bundle", size=12, pad=9, gap=6)
    s.box(x, t + 496, w, 70, "white", "FileInstall",
          ["`etc/*.cfg` become configurations (ConfigAdmin); one watcher", "per `org.apache.felix.fileinstall-*.cfg`: "
           "`deploy/`, the lab's folder"], seq=5)
    s.box(x, t + 580, w, 88, "white", "Features service: featuresBoot",
          ["`etc/org.apache.karaf.features.cfg`: 22 Karaf features first, then", "78 OpenNMS features (REST, "
           "api-layer, HTTP bridge, UIs, ...); a bundle", "without a start level of its own gets 80"], seq=6)
    s.box(x, t + 682, w, 62, "daemon", "Last boot feature: opennms-karaf-health",
          ["registers `KarafHealthService`, exported to OpenNMS: `KarafStartupMonitor` is done"], size=12.5,
          seq=7)
    for y1, y2 in ((t + 146, t + 158), (t + 266, t + 278), (t + 350, t + 362), (t + 482, t + 494),
                   (t + 566, t + 578), (t + 668, t + 680)):
        down(s, 334, y1, y2, "osgi")

    s.group(664, t, 412, 520, "white", "Karaf's folders are OpenNMS's folders")
    s.box(680, t + 40, 380, 140, "data", "`etc/`  (shared with OpenNMS)",
          ["`config.properties`, `custom.properties`,", "`startup.properties`,", "`org.apache.karaf.features.cfg`,",
           "every `*.cfg` (ConfigAdmin), the watchers", "`org.apache.felix.fileinstall-*.cfg`"])
    s.box(680, t + 192, 380, 70, "data", "`system/`", ["bundles and features XML in Maven layout:", "installs work offline"])
    s.box(680, t + 274, 380, 88, "data", "`data/`", ["`cache/`: installed bundles, `kar/`: unpacked KARs,",
                                                       "`tmp/`; not a volume in the image: rebuilt when", "the container is re-created"])
    s.box(680, t + 374, 380, 52, "data", "`deploy/`", ["Karaf's own hot-deploy folder"])
    s.box(680, t + 438, 184, 66, "data", "`logs/karaf.log`", ["Karaf's log"])
    s.box(876, t + 438, 184, 66, "data", "port `8101`", ["the SSH shell"])

    s.group(664, t + 540, 412, 220, "webapp", "Meanwhile, back in the web app", seq=8)
    s.box(680, t + 580, 380, 150, "white", lines=[
        "`launch()` has returned. WebAppListener stores", "the framework's `BundleContext` in the servlet",
        "context (the ProxyFilter finds it there) and", "starts the `OnmsOSGiBridgeActivator` (Step 11).",
        "The web app finishes starting; only then does", "Jetty open port 8980, while Karaf may still",
        "be installing features."], size=12.5)
    return s



# ------------------------------------------------------------------------------------------------
@diagram("07-felix")
def felix():
    s = Svg(1100, 790, "Felix, the OSGi framework under Karaf",
            "Felix implements the OSGi core: bundles with class loaders of their own, their life cycle, and a "
            "registry of services.\nKaraf is the distribution around it; several Felix sub-projects run inside it "
            "as ordinary bundles.")
    t = s.top() + 18
    s.group(24, t, 516, 472, "white", "The layers")
    s.box(40, t + 40, 484, 70, "karaf", "Karaf 4.3.10: the distribution",
          ["features and KARs, deployers, SSH shell, JAAS login,", "logging (Pax Logging), the files in `etc/`"])
    s.group(40, t + 124, 484, 282, "bundle", "Felix 6.0.5: the OSGi framework (core R7)")
    s.box(56, t + 162, 452, 70, "white", "Service layer", ["a registry of objects by interface name and",
                                                       "properties; LDAP-filter look-ups; change events"])
    s.box(56, t + 242, 452, 70, "white", "Life-cycle layer", ["install, resolve, start, stop, update,",
                                                          "uninstall; start levels set the boot order"])
    s.box(56, t + 322, 452, 70, "white", "Module layer", ["one class loader per bundle; each `Import-Package`",
                                                      "is wired to another bundle's `Export-Package`"])
    s.box(40, t + 420, 484, 38, "jvm", lines=["the JVM: the one OpenNMS process (Step 2)"], center=True)

    s.group(560, t, 516, 300, "white", "A bundle's life cycle")
    st = {"INSTALLED": (584, t + 56), "RESOLVED": (764, t + 56), "STARTING": (944, t + 56),
          "UNINSTALLED": (584, t + 176), "STOPPING": (764, t + 176), "ACTIVE": (944, t + 176)}
    for name, (x, y) in st.items():
        s.box(x, y, 116, 38, "plugin" if name == "ACTIVE" else "bundle", lines=[name], center=True, size=12.5)
    s.arrow([(700, t + 75), (762, t + 75)], "osgi", "resolve", lx=731, ly=t + 67)
    s.arrow([(880, t + 75), (942, t + 75)], "osgi", "start", lx=911, ly=t + 67)
    s.arrow([(1002, t + 94), (1002, t + 174)], "osgi")
    s.arrow([(942, t + 195), (882, t + 195)], "osgi", "stop", lx=911, ly=t + 187)
    s.arrow([(822, t + 174), (822, t + 96)], "osgi")
    s.arrow([(642, t + 94), (642, t + 174)], "osgi", "uninstall", lx=642, ly=t + 140)
    s.box(584, t + 232, 476, 56, "note", lines=["RESOLVED: every import is wired to an exporter.",
                                                "ACTIVE: started; Blueprint or DS build its services."],
          size=12.5)
    s.group(560, t + 316, 516, 156, "karaf", "The system bundle (id 0)")
    s.box(576, t + 352, 484, 104, "white", lines=[
        "the framework itself. It exports the JDK's packages plus", "the 1,383 packages listed in "
        "`etc/custom.properties`,", "183 of them `org.opennms.*`: bundles use the same classes", "from `lib/` as "
        "the daemons do (Steps 9 and 11)."], size=12.5)

    s.group(24, t + 490, 1052, 150, "karaf", "Felix sub-projects that run as bundles in OpenNMS")
    subs = [("FileInstall 3.7.4", ["watches folders:", "`etc/*.cfg`, `deploy/`"]),
            ("ConfigAdmin 1.9.26", ["configurations", "from `.cfg` files"]),
            ("HTTP bridge 4.1.6", ["servlets from bundles,", "inside Jetty (Step 12)"]),
            ("Metatype and more", ["helpers installed from", "`startup.properties`"]),
            ("Gogo", ["the command runtime", "of Karaf's shell"])]
    for i, (ti, li) in enumerate(subs):
        s.box(40 + i * 206, t + 528, 196, 70, "bundle", ti, li, title_size=13.5, size=12.5)
    s.text(40, t + 624, "Not Felix, used alongside: Aries Blueprint (XML wiring), Pax Logging, Pax URL "
           "(mvn: URLs), the JAX-RS connector.", size=12.5, color="#4c1d95")
    return s


# ------------------------------------------------------------------------------------------------
@diagram("08-packaging")
def packaging():
    s = Svg(1100, 760, "JARs, bundles, features, KARs: what a plugin is made of",
            "The lab's Node Inventory plugin, opened up. A KAR carries a features XML and the bundle; the bundle "
            "is a JAR\nwith OSGi headers, a Blueprint file, its class and the UI module.")
    t = s.top() + 18
    s.group(24, t, 596, 612, "plugin", "`opennms-lab-node-inventory-plugin.kar`: a ZIP", dash="7 5")
    s.box(40, t + 40, 564, 52, "white", "`META-INF/MANIFEST.MF`",
          ["`Karaf-Feature-Start: false` would stop the automatic install"])
    s.group(40, t + 106, 564, 490, "data", "`repository/`: a small Maven repository")
    s.box(56, t + 146, 532, 104, "white", "`.../node-inventory-karaf-features-...-features.xml`",
          ["a features repository with one feature,", "`opennms-lab-node-inventory`: the features `aries-blueprint`",
           "and `opennms-integration-api`, plus the bundle below"])
    s.group(56, t + 264, 532, 316, "bundle", "`.../node-inventory-plugin-1.0.0-SNAPSHOT.jar`: the bundle")
    s.box(72, t + 302, 500, 70, "white", "`META-INF/MANIFEST.MF`",
          ["`Bundle-SymbolicName`, `Bundle-Version`, and `Import-Package`:", "`org.opennms.integration.api.v1.ui`, ..."])
    s.box(72, t + 384, 500, 52, "white", "`OSGI-INF/blueprint/blueprint.xml`",
          ["registers a `UIExtension` service (Step 10)"])
    s.box(72, t + 448, 500, 52, "white", "`org/example/.../NodeInventoryUIExtension.class`",
          ["implements the Integration API interface `UIExtension`"])
    s.box(72, t + 512, 500, 52, "plugin", "`node-inventory/nodeInventory.es.js`",
          ["the UI module built by Vite (plus `style.css`), served at Step 13"])

    s.group(640, t, 436, 392, "white", "Five words")
    words = [("JAR", ["classes and files in a ZIP, plus a manifest;", "a class loader reads classes from it"]),
             ("Bundle", ["a JAR whose manifest names it, versions it and lists", "its imports and exports; Felix gives "
                                                                           "it a loader"]),
             ("Feature", ["a named set of bundles (and features, configuration)", "in a features XML, installed as "
                                                                              "one unit"]),
             ("KAR", ["a ZIP with a features XML and the bundles it needs,", "in Maven layout: installs offline"]),
             ("Plugin", ["for OpenNMS, usually a KAR whose bundle registers", "Integration API services"])]
    for i, (ti, li) in enumerate(words):
        s.box(656, t + 40 + i * 70, 404, 64, "note", ti, li, title_size=13.5, size=12.5)
    s.group(640, t + 408, 436, 204, "white", "Where each kind lives in the container")
    s.box(656, t + 446, 404, 150, "data", lines=[
        "`lib/*.jar`: plain JARs, the lib/ class loader", "`jetty-webapps/opennms/WEB-INF/lib/`: web app JARs",
        "`system/`: bundles and features XML (Maven layout)", "`deploy/`, `/opt/opennms-lab-deploy/`: KARs to install",
        "`data/kar/<name>/`: unpacked KARs", "`data/cache/bundle<id>/`: installed bundles"], size=12.5)
    return s


# ------------------------------------------------------------------------------------------------
@diagram("09-classloaders-threads")
def classloaders():
    s = Svg(1100, 880, "One process, many class loaders, many threads",
            "Plugins and bundles are not processes: they are class loaders and objects inside the one JVM. A "
            "request runs on one\nJetty thread from the socket to a plugin's JAR and back, crossing several class "
            "loaders on the way.")
    t = s.top() + 18
    s.group(24, t, 536, 580, "white", "Class loaders: each one reads from the places listed")
    s.box(40, t + 40, 504, 44, "grey", lines=["JDK: `java.*` and the other platform classes"], center=True)
    s.box(40, t + 98, 504, 44, "white", lines=["application loader: `lib/opennms_bootstrap.jar`"], center=True)
    s.box(40, t + 156, 504, 70, "daemon", "lib/ loader (Bootstrap's URLClassLoader)",
          ["`lib/*.jar`, `etc/`: daemons, Spring, Hibernate, Jetty, Karaf Main"])
    s.box(40, t + 250, 240, 96, "jetty", "Web app loader", ["Jetty's `WebAppClassLoader`:", "`WEB-INF/classes`,",
                                                          "`WEB-INF/lib` of `/opennms`"])
    s.box(304, t + 250, 240, 96, "karaf", "Karaf launcher loader", ["the Felix framework JAR;", "everything else",
                                                                  "from its parent"])
    for x in (160, 424):
        s.arrow([(x, t + 248), (x, t + 228)], "grey", sw=1.5)
    s.arrow([(292, t + 154), (292, t + 144)], "grey", sw=1.5)
    s.arrow([(292, t + 96), (292, t + 86)], "grey", sw=1.5)
    s.group(40, t + 370, 504, 194, "karaf", "Felix: one class loader per bundle")
    s.box(56, t + 406, 472, 34, "white", lines=["system bundle (0): classes via the launcher loader"], center=True,
          size=12.5)
    s.arrow([(424, t + 404), (424, t + 348)], "grey", sw=1.5)
    xs = {}
    x = 56
    for name, st in (("OIA API", "bundle"), ("api-layer", "bundle"), ("ui-extension", "bundle"),
                     ("Plugin A", "plugin"), ("Plugin B", "plugin")):
        w = round(text_width(name, 12.5) + 20)
        s.box(x, t + 494, w, 34, st, lines=[name], center=True, size=12.5)
        xs[name] = (x, w)
        x += w + 12
    ox, ow = xs["OIA API"]
    for nm in ("Plugin A", "Plugin B"):
        px, pw = xs[nm]
        s.arrow([(px + pw / 2, t + 530), (px + pw / 2, t + 540)], "osgi", sw=1.3, dash="4 3", end=False)
    pa, pb = xs["Plugin A"], xs["Plugin B"]
    s.arrow([(pb[0] + pb[1] / 2, t + 540), (ox + ow / 2, t + 540), (ox + ow / 2, t + 532)], "osgi", sw=1.3,
            dash="4 3")
    s.label((ox + pa[0]) / 2 + 40, t + 556, "Import-Package", size=11.5, color=ARROW["osgi"])
    ax, aw = xs["api-layer"]
    s.arrow([(ax + aw / 2, t + 492), (ax + aw / 2, t + 442)], "osgi", sw=1.3, dash="4 3")

    s.group(580, t, 496, 580, "white", "One request, one thread (a qtp thread)")
    frames = [("Jetty: connector, handlers, `/opennms` context", "daemon", "from `lib/`"),
              ("filter chain: headers, Spring Security, ...", "jetty", "web app"),
              ("`ProxyFilter`: the path is claimed in OSGi", "jetty", "web app"),
              ("Felix HTTP bridge: the dispatcher servlet", "bundle", "a bundle"),
              ("JAX-RS connector: finds the resource", "bundle", "bundles"),
              ("`UIExtensionServiceImpl`: the module file", "bundle", "ui-extension"),
              ("`Bundle.getResource(...)` in plugin A's JAR", "plugin", "plugin A")]
    for i, (txt, st, where) in enumerate(frames):
        y = t + 40 + i * 64
        s.box(596, y, 464, 50, st, lines=[txt, where], size=12.5)
        if i:
            down(s, 828, y - 14, y - 2)
    s.box(596, t + 500, 464, 54, "note", lines=["and back up the same stack with the response: no process",
                                               "boundary, no copy of the objects, one call stack"], size=12.5)

    s.group(24, t + 600, 1052, 144, "white", "Threads you will meet (scripts/karaf.sh shell:threads lists the live ones)")
    th = [("`Main`", ["the start-up, then", "it ends"]),
          ("`qtp<id>-<n>`", ["Jetty: one per", "request running"]),
          ("`FelixStartLevel`", ["starts and stops", "bundles by level"]),
          ("`FelixDispatchQueue`", ["delivers framework", "and bundle events"]),
          ("`fileinstall-<dir>`", ["one per watched", "folder"]),
          ("daemon threads", ["pollers, collectors", "and many more"])]
    for i, (ti, li) in enumerate(th):
        s.box(40 + i * 171, t + 638, 163, 90, "white", ti, li, title_size=13, size=12.5)
    return s



def note_on(s: Svg, x, y, w, lines, style="note", size=12.5):
    """A note box centred on a lifeline."""
    h = round(8 + size + (len(lines) - 1) * size * 1.38 + size * 0.25 + 8)
    s.box(round(x - w / 2), y, w, h, style, lines=lines, size=size)
    return y + h


# ------------------------------------------------------------------------------------------------
@diagram("10-deploy")
def deploy():
    s = Svg(1100, 940, "Deploying a plugin: from a file on your disk to a menu entry",
            "What happens, in order, after scripts/deploy-plugin.sh copies a KAR into ./deploy (no restart). "
            "Each column is a part\nof the one process, except the first; each blue number is one step of Step 10.")
    t = s.top() + 18
    xs = s.lanes(64, t, 1012, t + 680, [
        ("you", "You", ["host folder"], "host"), ("fi", "FileInstall", ["watcher thread"], "bundle"),
        ("kar", "KAR deployer", ["KarService"], "bundle"), ("feat", "Features", ["service"], "bundle"),
        ("felix", "Felix", ["framework"], "bundle"), ("bp", "Blueprint", ["Aries extender"], "bundle"),
        ("reg", "api-layer", ["UI registry"], "bundle"), ("rest", "REST + UI", ["`/rest/plugins`"], "jetty")])
    steps = []

    def m(a, b, y, text, kind="osgi", dash=None):
        s.msg(xs, a, b, y, text, kind, dash=dash)
        steps.append(y)

    def n(lane, y, w, lines):
        note_on(s, xs[lane], y, w, lines)
        steps.append(y + 14)

    m("you", "fi", t + 100, "copy a `.kar` into `./deploy/`", "plugin")
    m("fi", "kar", t + 150, "sees the new `.kar`: `install()`")
    n("kar", t + 172, 262, ["unpacks it into `data/kar/<name>/`", "and adds its features XML"])
    m("kar", "feat", t + 256, "install feature `opennms-lab-node-inventory`")
    m("feat", "felix", t + 306, "install and start the bundle")
    n("felix", t + 328, 292, ["INSTALLED (copied into `data/cache/`),", "RESOLVED (imports wired), ACTIVE"])
    m("felix", "bp", t + 412, "bundle is ACTIVE (event)")
    n("bp", t + 434, 272, ["reads `OSGI-INF/blueprint/*.xml`,", "creates the `UIExtension` bean"])
    m("bp", "felix", t + 518, "registers the `UIExtension` service")
    m("felix", "reg", t + 568, "service event: `onBind()`")
    m("rest", "reg", t + 618, "GET `/rest/plugins`", "http")
    m("reg", "rest", t + 660, "the list now has `labNodeInventory`", "http", dash="6 4")
    for i, y in enumerate(steps):
        s.seq(36, y - 4, i + 1)
    s.box(24, t + 700, 526, 96, "note", "Delete or replace the file",
          ["delete: the KAR, its features and the bundle are uninstalled;", "the service disappears and "
           "`onUnbind()` drops the plugin.", "replace: uninstall, then install the new file."], size=12.5)
    s.box(566, t + 700, 510, 96, "note", "In logs/karaf.log",
          ["`Installing KAR file /opt/opennms-lab-deploy/...`", "`Adding features: opennms-lab-node-inventory/...`",
           "`Done.`"], size=12.5)
    return s


# ------------------------------------------------------------------------------------------------
@diagram("11-services")
def services():
    s = Svg(1100, 810, "Two service registries and the bridge between them",
            "Daemons and the web app find each other in the OpenNMS service registry; bundles use the OSGi one. "
            "The bridge,\nstarted by the web app next to Karaf, copies registrations across in both directions.")
    t = s.top() + 18
    s.box(24, t, 320, 66, "daemon", "OpenNMS service registry",
          ["`DefaultServiceRegistry`: used by the", "Spring contexts and the web app"])
    s.box(372, t, 268, 66, "karaf", "OnmsOSGiBridgeActivator", ["started by WebAppListener,", "right after Karaf (Step 6)"])
    s.box(668, t, 408, 66, "karaf", "OSGi service registry (Felix)",
          ["used by every bundle: Blueprint references,", "service trackers, service listeners"])

    s.group(24, t + 88, 1052, 138, "white", "1. From OpenNMS to OSGi: every registration, for example the DAOs",
            label_size=13.5)
    s.box(40, t + 124, 290, 88, "daemon", "daoContext (Spring)",
          ["bean `nodeDao`, published with", "`<onmsgi:service interface=`", "`\"...netmgt.dao.api.NodeDao\">`"])
    s.box(372, t + 124, 268, 88, "white", lines=["registered in OSGi as well, by", "the system bundle, with",
                                                 "`registration.source=onms`"])
    s.box(668, t + 124, 392, 88, "bundle", "api-layer (Blueprint)",
          ["`<reference interface=\"...dao.api.NodeDao\">`", "wraps it and registers the Integration API's",
           "`org.opennms.integration.api.v1.dao.NodeDao`"])
    s.arrow([(330, t + 168), (370, t + 168)], "osgi")
    s.arrow([(640, t + 168), (666, t + 168)], "osgi")

    s.group(24, t + 242, 1052, 124, "white", "2. From OSGi to OpenNMS: only services marked registration.export",
            label_size=13.5)
    s.box(668, t + 278, 392, 72, "bundle", "karaf-health bundle",
          ["registers `KarafHealthService` with", "`registration.export=true`"])
    s.box(372, t + 278, 268, 72, "white", lines=["registered in the OpenNMS", "registry as well, with",
                                                 "`registration.source=osgi`"])
    s.box(40, t + 278, 290, 72, "daemon", "KarafStartupMonitor", ["waits for it (Step 3)"])
    s.arrow([(666, t + 314), (642, t + 314)], "osgi")
    s.arrow([(370, t + 314), (332, t + 314)], "daemon")

    s.group(24, t + 382, 1052, 112, "white", "3. The same way: a menu link that comes from a bundle", label_size=13.5)
    s.box(668, t + 418, 392, 62, "bundle", "dashboard bundle (Vaadin)",
          ["a `PageNavEntry` for `Page=admin`, exported"])
    s.box(40, t + 418, 290, 62, "jetty", "admin/index.jsp", ["links for `(Page=admin)` entries"])
    s.arrow([(666, t + 449), (332, t + 449)], "osgi")
    s.label(506, t + 443, "copied like 2.", color=ARROW["osgi"])

    s.group(24, t + 510, 1052, 158, "white", "4. Inside OSGi only: the UI extensions are never exported",
            label_size=13.5)
    boxes = [(40, 230, "plugin", "Plugins A and B", ["each registers a", "`UIExtension` service"]),
             (292, 250, "bundle", "api-layer", ["a `reference-list` of", "`UIExtension`s: `onBind()`",
                                                "fills `UIExtensionRegistry`"]),
             (564, 250, "bundle", "ui-extension", ["`UIExtensionService`, a JAX-RS", "resource with",
                                                   "`application-path=/rest`"]),
             (836, 224, "bundle", "JAX-RS connector", ["publishes it under", "`/opennms/rest/plugins`",
                                                       "(Steps 12 and 13)"])]
    for x, w, st, ti, li in boxes:
        s.box(x, t + 548, w, 102, st, ti, li)
    for x1, x2 in ((270, 290), (542, 562), (814, 834)):
        s.arrow([(x1, t + 599), (x2, t + 599)], "osgi")
    return s


# ------------------------------------------------------------------------------------------------
@diagram("12-jetty-felix")
def jetty_felix():
    s = Svg(1100, 948, "Jetty and Felix: how a request gets from the network into OSGi",
            "The only way in is Jetty's port. The ProxyFilter, last in the web app's filter chain, sends paths that "
            "OSGi has claimed\nto the Felix HTTP bridge; the bridge opens no port of its own and runs on Jetty's "
            "request thread.")
    t = s.top() + 18
    s.box(400, t, 300, 44, "white", lines=["Browser: `GET /opennms/...`"], center=True)
    s.box(400, t + 68, 300, 58, "jetty", "Jetty, port 8980", ["context `/opennms` (Step 4)"], seq=1)
    s.box(400, t + 150, 300, 58, "jetty", "Filters of the web app", ["Spring Security first (Step 5)"], seq=2)
    s.box(330, t + 232, 440, 100, "karaf", "ProxyFilter: claimed by OSGi?",
          ["yes if the path matches a JAX-RS resource published", "in OSGi, a whiteboard servlet pattern or a",
           "whiteboard resource pattern"], seq=3)
    for y1, y2 in ((t + 44, t + 66), (t + 126, t + 148), (t + 208, t + 230)):
        down(s, 550, y1, y2, "http")
    s.arrow([(330, t + 282), (274, t + 282), (274, t + 382)], "http")
    s.label(274, t + 362, "no: chain.doFilter()", color=ARROW["http"])
    s.arrow([(770, t + 282), (826, t + 282), (826, t + 382)], "osgi")
    s.label(826, t + 362, "yes: dispatcher.service()", color=ARROW["osgi"])

    s.group(24, t + 384, 500, 300, "jetty", "The web app's own servlets", seq=4)
    s.box(40, t + 422, 468, 70, "white", "Apache CXF", ["`/rest/*`, `/api/v2/*`: the OpenNMS REST API",
                                                     "(nodes, events, alarms, ...)"])
    s.box(40, t + 504, 468, 70, "white", "Spring MVC and JSP", ["`*.htm`, `*.jsp`: the classic UI"])
    s.box(40, t + 586, 468, 82, "white", "DefaultServlet", ["files: the Vue UI in `ui/`, `assets/`,",
                                                         "the lab's `assets/shared/` (Step 14)"])
    s.group(576, t + 384, 500, 300, "karaf", "Felix HTTP bridge (a bundle)", seq=5)
    s.box(592, t + 422, 468, 64, "white", "Dispatcher servlet",
          ["an OSGi service (`HttpServlet`, `http.felix.dispatcher`)", "that the ProxyFilter keeps track of"])
    s.box(592, t + 498, 468, 58, "bundle", "JAX-RS connector (Jersey)",
          ["`/rest/plugins`, `/rest/health`, ...: resources in bundles"])
    s.box(592, t + 566, 468, 50, "bundle", "Whiteboard servlets",
          ["Vaadin apps, e.g. `/admin/wallboard-config/*`"])
    s.box(592, t + 626, 468, 44, "bundle", lines=["Whiteboard resources: files packed in bundles"])

    s.box(24, t + 704, 526, 110, "note", "How the web app finds Felix",
          ["WebAppListener put the `BundleContext` into the servlet", "context (Step 6); `ServiceTracker`s follow "
           "the dispatcher,", "servlets and resources; REST paths come from the", "`RestEndpointRegistry` service"],
          size=12.5)
    s.box(566, t + 704, 510, 110, "note", "No second web server",
          ["OSGi servlets run on the Jetty thread, behind the same", "filters and the same login. Other ports in this "
           "process", "are not HTTP: Karaf SSH `8101`, SNMP traps `1162/udp`."], size=12.5)
    return s



# ------------------------------------------------------------------------------------------------
@diagram("13-plugin-uis")
def plugin_uis():
    s = Svg(1100, 800, "Plugin A and plugin B: many UIs from one server",
            "Both plugins are served by the same Jetty, the same /opennms web app and the same REST endpoint. The "
            "extension id in\nthe URL decides which bundle's JAR the file comes from; routes after # never reach "
            "the server.")
    t = s.top() + 18
    s.group(24, t, 300, 470, "white", "Browser: the Vue UI")
    s.box(40, t + 40, 268, 196, "grey", "`/opennms/ui/`", ["menu Plugins:", "- Shared Assets: Node Inventory",
                                                          "- Shared Assets: Icon Catalog", "",
                                                          "one route per plugin, handled", "in the browser:"])
    s.box(40, t + 252, 268, 94, "plugin", "Node Inventory (A)", ["`#/plugins/labNodeInventory/`",
                                                                  "`node-inventory/`", "`nodeInventory.es.js`"])
    s.box(40, t + 360, 268, 94, "plugin", "Icon Catalog (B)", ["`#/plugins/labIconCatalog/`", "`icon-catalog/`",
                                                                "`iconCatalog.es.js`"])

    s.group(344, t, 400, 470, "jetty", "Requests to the one server (port 8980)")
    rows = [("`GET /opennms/ui/`", ["DefaultServlet: `ui/index.html`, `ui/assets/*`"], "white"),
            ("`GET /opennms/rest/plugins`", ["OSGi: the registry, as JSON: A and B"], "bundle"),
            ("`GET .../ui-extension/module/`", ["`labNodeInventory`", "`?path=node-inventory/nodeInventory.es.js`"],
             "plugin"),
            ("`GET .../ui-extension/module/`", ["`labIconCatalog`", "`?path=icon-catalog/iconCatalog.es.js`"],
             "plugin"),
            ("`GET .../ui-extension/css/labNodeInventory`", ["`node-inventory/style.css` of A"], "plugin")]
    ys = []
    y = t + 40
    for ti, li, st in rows:
        h = 52 if len(li) == 1 else 70
        s.box(360, y, 368, h, st, ti, li, title_size=13, size=12.5, seq=len(ys) + 1)
        ys.append((y, h))
        y += h + 12

    s.group(764, t, 312, 470, "white", "Two bundles, two JARs")
    s.box(780, t + 40, 280, 150, "plugin", "Node Inventory bundle",
          ["`UIExtension` id `labNodeInventory`", "root `node-inventory`", "JAR entries:",
           "`node-inventory/nodeInventory.es.js`", "`node-inventory/style.css`"], size=12.5)
    s.box(780, t + 206, 280, 132, "plugin", "Icon Catalog bundle",
          ["`UIExtension` id `labIconCatalog`", "root `icon-catalog`", "JAR entry:",
           "`icon-catalog/iconCatalog.es.js`"], size=12.5)
    s.box(780, t + 354, 280, 100, "note", "How an id finds a JAR",
          ["the registry gives the extension,", "`getExtensionClass()` its bundle,", "`bundle.getResource(path)` the file"],
          size=12.5)
    (ya, ha), (yb, hb) = ys[2], ys[3]
    s.arrow([(728, ya + ha / 2), (746, ya + ha / 2), (746, t + 100), (778, t + 100)], "plugin")
    s.arrow([(728, yb + hb / 2), (756, yb + hb / 2), (756, t + 260), (778, t + 260)], "plugin")
    yc, hc = ys[4]
    s.arrow([(728, yc + hc / 2), (738, yc + hc / 2), (738, t + 170), (778, t + 170)], "plugin", dash="4 3")

    s.group(24, t + 490, 1052, 180, "white", "Other ways a bundle puts a UI or an API on the same server")
    other = [("JAX-RS resource", ["JSON or text under `/opennms/rest/...`,", "like `UIExtensionService` itself",
                                  "(Step 12)"]),
             ("Whiteboard servlet", ["a whole page, e.g. the Vaadin", "wallboard configuration at",
                                     "`/opennms/admin/wallboard-config/`"]),
             ("PageNavEntry service", ["a link in the classic admin page,", "exported to the OpenNMS registry",
                                       "(Step 11)"])]
    for i, (ti, li) in enumerate(other):
        s.box(40 + i * 346, t + 528, 330, 124, "bundle", ti, li, size=12.5)
    return s


# ------------------------------------------------------------------------------------------------
@diagram("14-shared-assets")
def shared_assets():
    s = Svg(1100, 750, "Shared assets: one folder, served by Jetty, read by every plugin in the browser",
            "No OSGi and no Java code of yours: the folder is a directory inside the /opennms web app, served "
            "like OpenNMS's\nown JavaScript. Plugins find the files through a fixed URL and the index "
            "manifest.json.")
    t = s.top() + 18
    s.group(24, t, 292, 330, "host", "Your machine")
    s.box(40, t + 40, 260, 180, "assets", "`./shared-assets/`",
          ["`manifest.json`: the index,", "with `revision` and the rules", "`icons/router.svg`, `switch.svg`, ...",
           "`branding/lab-banner.png`", "", "edited with `scripts/assets.py`"], size=12.5)
    s.box(40, t + 236, 260, 76, "note", lines=["new file: served at once", "changed file: bump `revision`,",
                                               "every `?rev=` changes"], size=12.5)
    s.group(336, t, 404, 520, "container", "Container: the /opennms web app", dash="7 5")
    s.box(352, t + 40, 372, 70, "assets", "`jetty-webapps/opennms/assets/shared/`",
          ["the same folder, mounted read-only"], size=12.5)
    s.box(352, t + 132, 372, 88, "jetty", "Jetty and the filters", ["no login needed for `/assets/**`,",
                                                                     "`nosniff`, CSP of the UI's own origin"],
          size=12.5)
    s.box(352, t + 242, 372, 106, "jetty", "DefaultServlet", ["reads the file from disk on each request",
                                                               "(cached by modification time);",
                                                               "`Cache-Control: max-age=3600,public`"], size=12.5)
    s.box(352, t + 370, 372, 130, "white", "URL", ["`/opennms/assets/shared/manifest.json`",
                                                   "`/opennms/assets/shared/icons/router.svg`",
                                                   "", "same origin as the UI, so the UI's", "CSP (`img-src 'self'`) allows it"],
          size=12.5)
    s.arrow([(300, t + 130), (318, t + 130), (318, t + 75), (350, t + 75)], "assets", dash="6 4")
    down(s, 538, t + 110, t + 130, "assets")
    down(s, 538, t + 220, t + 240, "assets")
    down(s, 538, t + 348, t + 368, "assets")

    s.group(760, t, 316, 520, "white", "Who reads it (all in the browser)")
    s.box(776, t + 40, 284, 120, "plugin", "Plugin A's JavaScript",
          ["the shared helper: `GET manifest.json`", "(`no-cache`: a 304 when unchanged),", "then `<img>` URLs with `?rev=1`"],
          size=12.5)
    s.box(776, t + 172, 284, 88, "plugin", "Plugin B's JavaScript", ["the same helper, the same URLs:", "one browser cache for both"],
          size=12.5)
    s.box(776, t + 272, 284, 88, "white", "Any page or tool", ["`<img src=\"/opennms/assets/...\">`,", "the classic UI, curl"],
          size=12.5)
    s.box(776, t + 372, 284, 128, "grey", "Not involved", ["Karaf, Felix, bundles and the", "plugin JARs: no Java code",
                                                         "reads the folder, nothing is", "deployed for a new image"],
          size=12.5)
    s.arrow([(724, t + 435), (744, t + 435), (744, t + 100), (774, t + 100)], "assets")
    s.arrow([(744, t + 216), (774, t + 216)], "assets")
    s.arrow([(744, t + 316), (774, t + 316)], "assets")

    s.box(24, t + 352, 292, 168, "note", "Why not inside a plugin JAR?",
          ["the module endpoint serves only", "the module (as JavaScript) and", "`style.css`: images do not work",
           "there, and every plugin would", "carry its own copy (Part 1)"], size=12.5)
    s.box(24, t + 540, 1052, 76, "note", "The contract every plugin relies on (Part 3)",
          ["a fixed base URL, `/opennms/assets/shared/`, plus `manifest.json` as the index of files and node-icon "
           "rules; the helper package", "`@onms-lab/shared-assets` is compiled into each plugin's JavaScript, so "
           "the plugins share files, not code at run time."], size=12.5)
    return s



# ------------------------------------------------------------------------------------------------
@diagram("15-page-load")
def page_load():
    s = Svg(1100, 948, "One page load, end to end",
            "Opening the Node Inventory plugin in the Vue UI. Every request first passes Jetty's handlers and the "
            "web app's filters\n(Steps 4 and 5); the columns show which part answers. Dashed arrows are the answers.")
    t = s.top() + 18
    xs = s.lanes(64, t, 1012, t + 736, [
        ("b", "Browser", ["`/opennms/ui/`"], "white"), ("ds", "DefaultServlet", ["static files"], "jetty"),
        ("pf", "ProxyFilter", ["Felix, JAX-RS"], "karaf"), ("ux", "ui-extension", ["plugin JARs"], "bundle"),
        ("cxf", "Apache CXF", ["REST API v2"], "jetty"), ("db", "PostgreSQL", ["database"], "data"),
        ("fs", "Shared folder", ["your disk"], "assets")])
    rows = []

    def r(a, b, y, text, kind, dash=None, at="start", num=True):
        s.msg(xs, a, b, y, text, kind, dash=dash, at=at)
        if num:
            rows.append(y)

    r("b", "ds", t + 100, "`GET /opennms/ui/`, then its JS and CSS", "http")
    r("ds", "b", t + 136, "`index.html`, the UI's code", "http", dash="6 4", num=False)
    r("b", "pf", t + 186, "`GET /opennms/rest/plugins`", "osgi")
    r("pf", "ux", t + 222, "JAX-RS", "osgi", at="middle", num=False)
    r("ux", "b", t + 258, "JSON: `labNodeInventory`, `labIconCatalog`", "osgi", dash="6 4", num=False)
    r("b", "pf", t + 308, "`GET .../module/labNodeInventory?path=...`", "plugin")
    r("pf", "ux", t + 344, "JAX-RS", "plugin", at="middle", num=False)
    r("ux", "b", t + 380, "plugin A's module (JavaScript)", "plugin", dash="6 4", num=False)
    s.label(xs["b"] + 10, t + 408, "(the same for labIconCatalog)", color="#64748b", anchor="start")
    r("b", "pf", t + 450, "`GET .../css/labNodeInventory` (route opened)", "plugin")
    r("ux", "b", t + 486, "`style.css` from plugin A's JAR", "plugin", dash="6 4", num=False)
    r("b", "ds", t + 536, "`GET /opennms/assets/shared/manifest.json`", "assets")
    r("ds", "fs", t + 572, "reads the file", "assets", at="middle", num=False)
    r("ds", "b", t + 600, "JSON, `no-cache`: 304 next time", "assets", dash="6 4", num=False)
    r("b", "cxf", t + 646, "`GET /opennms/api/v2/nodes`", "http")
    r("cxf", "db", t + 682, "SQL (Hibernate)", "data", at="middle", num=False)
    r("cxf", "b", t + 714, "JSON: the nodes", "http", dash="6 4", num=False)
    for i, y in enumerate(rows):
        s.seq(36, y - 4, i + 1)
    s.box(24, t + 752, 1052, 76, "note", "Then the images", [
        "`GET /opennms/assets/shared/icons/router.svg?rev=1` for each node: the DefaultServlet answers from the "
        "shared folder as in", "step 5, then the browser keeps the file for an hour. The page never asks Karaf for "
        "an image, and never talks to PostgreSQL itself."], size=12.5, seq=7)
    return s


# ------------------------------------------------------------------------------------------------
@diagram("16-around")
def around():
    s = Svg(1100, 800, "Around the core: what else the process talks to",
            "The one OpenNMS process and its neighbours; Step 16 explains each box. In this lab only PostgreSQL "
            "runs in a\ncontainer of its own.")
    t = s.top() + 18
    s.group(380, t + 196, 340, 238, "jvm", "The OpenNMS JVM", sw=2.6)
    s.box(396, t + 234, 308, 56, "daemon", "Daemons", ["`Eventd`: the event bus in the process"], size=12.5)
    s.box(396, t + 300, 308, 56, "jetty", "Jetty and the web app", ["Spring Security: web UI and REST"], size=12.5)
    s.box(396, t + 366, 308, 56, "karaf", "Karaf and Felix", ["OSGi bundles, plugins, SSH shell"], size=12.5)
    sat = [
        (24, t, "host", "People and tools", ["browsers and REST clients: `8980`", "Karaf shell over SSH: `8101`",
                                              "the same accounts: `etc/users.xml`"]),
        (756, t, "grey", "Network devices", ["polled and collected from (ICMP,", "SNMP, HTTP, ...); SNMP traps",
                                             "arrive on `1162/udp` (Trapd)"]),
        (24, t + 250, "data", "Configuration: `etc/`", ["XML and properties for the daemons,", "Karaf's `.cfg` files "
                                                         "(ConfigAdmin)", "a volume in this lab: `onms-etc`"]),
        (756, t + 250, "data", "PostgreSQL", ["nodes, events, alarms, outages, ...", "schema by the installer (Step 2)",
                                              "one pool: the `dataSource`"]),
        (24, t + 500, "data", "Logs: `logs/`", ["one file per prefix: `manager.log`,", "`web.log`, `jetty-server.log`, ...",
                                                "and `karaf.log` from Pax Logging"]),
        (756, t + 500, "data", "Time series: `/opennms-data/rrd/`", ["RRD files (RRDtool) in the image's",
                                                                      "default strategy; graphs read", "them back"]),
    ]
    for x, y, st, ti, li in sat:
        s.box(x, y, 320, 100, st, ti, li, size=12.5)
    s.box(380, t + 540, 340, 124, "karaf", "Minion and Sentinel (not in the lab)",
          ["separate Karaf processes built from", "the same kind of bundles: polling near", "devices, or scaled-out "
           "processing;", "they reach the core over a broker or gRPC"], size=12.5)
    cx, cy = 550, t + 315
    for (x1, y1), (x2, y2), kind, both in [((344, t + 50), (400, t + 196), "http", False),
                                           ((756, t + 50), (700, t + 196), "grey", True),
                                           ((344, t + 300), (378, t + 300), "data", True),
                                           ((756, t + 300), (722, t + 300), "data", True),
                                           ((400, t + 436), (344, t + 550), "data", False),
                                           ((756, t + 550), (700, t + 436), "data", True),
                                           ((550, t + 538), (550, t + 436), "osgi", False)]:
        s.arrow([(x1, y1), (x2, y2)], kind, dash="5 4" if kind == "osgi" else None, start=both)
    return s


def main() -> int:
    check = "--check" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    stale, warned = [], False
    for name, fn in DIAGRAMS.items():
        if only and name not in only:
            continue
        out = OUT / f"{name}.svg"
        svg_obj = fn()
        svg = svg_obj.render()
        for w in svg_obj.warnings:
            print(f"warning {name}: {w}")
            warned = True
        if check:
            if not out.exists() or out.read_text(encoding="utf-8") != svg:
                stale.append(out.name)
        else:
            out.write_text(svg, encoding="utf-8")
            print("wrote", out.relative_to(OUT.parent.parent.parent))
    if check and stale:
        print("out of date:", ", ".join(stale), "- run make_diagrams.py")
        return 1
    return 1 if (check and warned) else 0


if __name__ == "__main__":
    sys.exit(main())
