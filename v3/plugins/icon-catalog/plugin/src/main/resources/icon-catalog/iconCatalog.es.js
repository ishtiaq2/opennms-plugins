const k = "/opennms/assets/shared/";
function M(e) {
  return e.endsWith("/") ? e : `${e}/`;
}
function I(e, n = {}) {
  const a = M(n.base ?? k), r = e.replace(/^\/+/, ""), i = r.split("/");
  if (r === "" || i.some((g) => g === "" || g === "." || g === ".."))
    throw new Error(`Invalid shared asset path: "${e}"`);
  const l = i.map((g) => encodeURIComponent(g)).join("/"), h = n.revision !== void 0 && n.revision !== null && `${n.revision}` != "" ? `?rev=${encodeURIComponent(String(n.revision))}` : "";
  return `${a}${l}${h}`;
}
const A = Object.freeze({
  schemaVersion: 1,
  revision: "",
  icons: {},
  images: {},
  nodeIconRules: [],
  defaultIcon: "unknown"
}), T = "__onmsLabSharedAssets__";
function R() {
  const e = globalThis;
  let n = e[T];
  return n || (n = { manifests: /* @__PURE__ */ new Map() }, e[T] = n), n;
}
function N(e = {}) {
  const n = M(e.base ?? k), a = R(), r = e.force ? void 0 : a.manifests.get(n);
  if (r)
    return r;
  const l = (e.fetchImpl ?? globalThis.fetch.bind(globalThis))(`${n}manifest.json`, {
    cache: "no-cache",
    credentials: "same-origin",
    headers: { Accept: "application/json" }
  }).then((s) => {
    if (!s.ok)
      throw new Error(`GET ${n}manifest.json -> HTTP ${s.status}`);
    return s.json();
  }).then((s) => x(s)).catch((s) => (a.manifests.delete(n), console.warn("[shared-assets] manifest unavailable, using an empty one:", s), A));
  return a.manifests.set(n, l), l;
}
function v(e) {
  return typeof e == "object" && e !== null && !Array.isArray(e);
}
function C(e, n) {
  const a = {};
  if (e === void 0)
    return a;
  if (!v(e))
    throw new Error(`manifest.${n} must be an object`);
  for (const [r, i] of Object.entries(e))
    v(i) && typeof i.path == "string" && i.path.length > 0 ? a[r] = { path: i.path, label: typeof i.label == "string" ? i.label : void 0 } : console.warn(`[shared-assets] ignoring manifest.${n}.${r}: missing "path"`);
  return a;
}
function V(e) {
  return Array.isArray(e) ? e.filter((n) => typeof n == "string") : void 0;
}
function x(e) {
  if (!v(e))
    throw new Error("manifest.json must contain a JSON object");
  if (e.schemaVersion !== 1)
    throw new Error(`unsupported schemaVersion ${String(e.schemaVersion)} (expected 1)`);
  const n = C(e.icons, "icons"), a = C(e.images, "images"), r = [];
  if (Array.isArray(e.nodeIconRules))
    for (const s of e.nodeIconRules) {
      if (!v(s) || typeof s.icon != "string" || !v(s.match)) {
        console.warn("[shared-assets] ignoring malformed rule", s);
        continue;
      }
      const h = s.match;
      r.push({
        icon: s.icon,
        match: {
          categories: V(h.categories),
          sysObjectIdPrefixes: V(h.sysObjectIdPrefixes),
          foreignSources: V(h.foreignSources),
          labelPattern: typeof h.labelPattern == "string" ? h.labelPattern : void 0
        }
      });
    }
  const i = typeof e.revision == "number" || typeof e.revision == "string" ? e.revision : "", l = typeof e.defaultIcon == "string" ? e.defaultIcon : "unknown";
  return { schemaVersion: 1, revision: i, icons: n, images: a, nodeIconRules: r, defaultIcon: l };
}
const O = window.Vue.defineComponent, t = window.Vue.createElementVNode, c = window.Vue.toDisplayString, L = window.Vue.unref, p = window.Vue.createTextVNode, f = window.Vue.openBlock, _ = window.Vue.createElementBlock, y = window.Vue.createCommentVNode, E = window.Vue.renderList, S = window.Vue.Fragment, B = window.Vue.normalizeClass, D = window.Vue.vModelText, U = window.Vue.withDirectives, F = window.Vue.withModifiers, j = window.Vue.pushScopeId, z = window.Vue.popScopeId, w = (e) => (j("data-v-e47355bd"), e = e(), z(), e), H = { class: "lab-ic" }, J = /* @__PURE__ */ w(() => /* @__PURE__ */ t("h1", { class: "lab-ic__title" }, "Shared Icon Catalog", -1)), W = { class: "lab-ic__muted" }, q = /* @__PURE__ */ w(() => /* @__PURE__ */ t("code", null, "manifest.json", -1)), G = { key: 0 }, Y = {
  key: 1,
  class: "lab-ic__grid"
}, K = ["src", "alt", "width", "height"], Q = { key: 0 }, X = /* @__PURE__ */ w(() => /* @__PURE__ */ t("br", null, null, -1)), Z = { class: "lab-ic__section" }, ee = /* @__PURE__ */ w(() => /* @__PURE__ */ t("h2", null, "Probe a path", -1)), te = /* @__PURE__ */ w(() => /* @__PURE__ */ t("p", { class: "lab-ic__muted" }, [
  /* @__PURE__ */ p(" Copy a file into the host folder "),
  /* @__PURE__ */ t("code", null, "shared-assets/"),
  /* @__PURE__ */ p(", type its path and press Check. Jetty serves it on the next request: no restart, no rebuild, no manifest edit needed for a direct URL. ")
], -1)), ne = ["onSubmit"], oe = /* @__PURE__ */ w(() => /* @__PURE__ */ t("button", { type: "submit" }, "Check", -1)), se = {
  key: 0,
  class: "lab-ic__error"
}, ae = { key: 1 }, ie = ["src"], ce = { class: "lab-ic__section" }, re = /* @__PURE__ */ w(() => /* @__PURE__ */ t("h2", null, "Node icon rules", -1)), le = { class: "lab-ic__muted" }, de = { class: "lab-ic__table" }, ue = /* @__PURE__ */ w(() => /* @__PURE__ */ t("thead", null, [
  /* @__PURE__ */ t("tr", null, [
    /* @__PURE__ */ t("th", null, "#"),
    /* @__PURE__ */ t("th", null, "Icon"),
    /* @__PURE__ */ t("th", null, "When")
  ])
], -1)), he = window.Vue.computed, fe = window.Vue.onMounted, b = window.Vue.ref, _e = /* @__PURE__ */ O({
  __name: "IconCatalog",
  setup(e) {
    const n = b(A), a = b([]), r = b(!0), i = b("icons/"), l = b(null), s = b(""), h = b("");
    async function g(d) {
      const u = await fetch(d, { method: "HEAD", cache: "no-store", credentials: "same-origin" });
      return {
        status: u.status,
        contentType: u.headers.get("content-type") ?? "-",
        cacheControl: u.headers.get("cache-control") ?? "-",
        lastModified: u.headers.get("last-modified") ?? "-"
      };
    }
    fe(async () => {
      const d = await N();
      n.value = d;
      const u = [];
      for (const [o, m] of Object.entries(d.icons))
        u.push({ key: o, kind: "icon", label: m.label ?? o, path: m.path, url: I(m.path, { revision: d.revision }) });
      for (const [o, m] of Object.entries(d.images ?? {}))
        u.push({ key: o, kind: "image", label: m.label ?? o, path: m.path, url: I(m.path, { revision: d.revision }) });
      a.value = u, r.value = !1, await Promise.all(
        u.map(async (o) => {
          try {
            o.head = await g(o.url);
          } catch {
            o.head = { status: 0, contentType: "network error", cacheControl: "-", lastModified: "-" };
          }
        })
      ), a.value = [...u];
    });
    async function $() {
      h.value = "", l.value = null, s.value = "";
      try {
        const d = I(i.value);
        l.value = await g(d), s.value = d;
      } catch (d) {
        h.value = d instanceof Error ? d.message : String(d);
      }
    }
    const P = he(
      () => l.value !== null && l.value.status === 200 && l.value.contentType.startsWith("image/")
    );
    return (d, u) => (f(), _("div", H, [
      J,
      t("p", W, [
        p(" Every entry of "),
        q,
        p(" (revision "),
        t("code", null, c(n.value.revision === "" ? "n/a" : n.value.revision), 1),
        p("), served by Jetty from "),
        t("code", null, c(L(k)), 1),
        p(". The Node Inventory plugin renders the same files. ")
      ]),
      r.value ? (f(), _("p", G, "Loading manifest...")) : (f(), _("div", Y, [
        (f(!0), _(S, null, E(a.value, (o) => (f(), _("figure", {
          key: o.kind + ":" + o.key,
          class: "lab-ic__card"
        }, [
          t("img", {
            src: o.url,
            alt: o.label,
            class: B(o.kind === "image" ? "lab-ic__wide" : ""),
            width: o.kind === "image" ? 240 : 64,
            height: o.kind === "image" ? 48 : 64,
            "data-shared-asset": "catalog"
          }, null, 10, K),
          t("figcaption", null, [
            t("strong", null, c(o.key), 1),
            t("span", null, c(o.label), 1),
            t("code", null, c(o.path), 1),
            o.head ? (f(), _("small", Q, [
              p(" HTTP " + c(o.head.status) + " | " + c(o.head.contentType), 1),
              X,
              p(" Cache-Control: " + c(o.head.cacheControl), 1)
            ])) : y("", !0)
          ])
        ]))), 128))
      ])),
      t("section", Z, [
        ee,
        te,
        t("form", {
          class: "lab-ic__probe",
          onSubmit: F($, ["prevent"])
        }, [
          U(t("input", {
            "onUpdate:modelValue": u[0] || (u[0] = (o) => i.value = o),
            placeholder: "icons/my-new-icon.svg",
            "aria-label": "Path relative to the shared folder"
          }, null, 512), [
            [D, i.value]
          ]),
          oe
        ], 40, ne),
        h.value ? (f(), _("p", se, c(h.value), 1)) : y("", !0),
        l.value ? (f(), _("p", ae, [
          t("code", null, c(s.value), 1),
          p(" -> HTTP " + c(l.value.status) + " | " + c(l.value.contentType) + " | Last-Modified: " + c(l.value.lastModified), 1)
        ])) : y("", !0),
        P.value ? (f(), _("img", {
          key: 2,
          src: s.value,
          alt: "probe result",
          width: "64",
          height: "64",
          "data-shared-asset": "probe"
        }, null, 8, ie)) : y("", !0)
      ]),
      t("section", ce, [
        re,
        t("p", le, [
          p("Evaluated top to bottom; the first match wins. Default icon: "),
          t("code", null, c(n.value.defaultIcon), 1),
          p(".")
        ]),
        t("table", de, [
          ue,
          t("tbody", null, [
            (f(!0), _(S, null, E(n.value.nodeIconRules, (o, m) => (f(), _("tr", { key: m }, [
              t("td", null, c(m + 1), 1),
              t("td", null, [
                t("code", null, c(o.icon), 1)
              ]),
              t("td", null, [
                t("code", null, c(JSON.stringify(o.match)), 1)
              ])
            ]))), 128))
          ])
        ])
      ])
    ]));
  }
}), pe = (e, n) => {
  const a = e.__vccOpts || e;
  for (const [r, i] of n)
    a[r] = i;
  return a;
}, me = /* @__PURE__ */ pe(_e, [["__scopeId", "data-v-e47355bd"]]);
window.labIconCatalog = me;
