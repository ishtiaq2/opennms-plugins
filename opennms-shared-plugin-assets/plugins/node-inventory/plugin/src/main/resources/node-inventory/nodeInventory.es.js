const p = "/opennms/assets/shared/";
function k(e) {
  return e.endsWith("/") ? e : `${e}/`;
}
function $(e, n = {}) {
  const t = k(n.base ?? p), o = e.replace(/^\/+/, ""), r = o.split("/");
  if (o === "" || r.some((g) => g === "" || g === "." || g === ".."))
    throw new Error(`Invalid shared asset path: "${e}"`);
  const u = r.map((g) => encodeURIComponent(g)).join("/"), c = n.revision !== void 0 && n.revision !== null && `${n.revision}` != "" ? `?rev=${encodeURIComponent(String(n.revision))}` : "";
  return `${t}${u}${c}`;
}
const A = Object.freeze({
  schemaVersion: 1,
  revision: "",
  icons: {},
  images: {},
  nodeIconRules: [],
  defaultIcon: "unknown"
}), I = "__onmsLabSharedAssets__";
function T() {
  const e = globalThis;
  let n = e[I];
  return n || (n = { manifests: /* @__PURE__ */ new Map() }, e[I] = n), n;
}
function P(e = {}) {
  const n = k(e.base ?? p), t = T(), o = e.force ? void 0 : t.manifests.get(n);
  if (o)
    return o;
  const u = (e.fetchImpl ?? globalThis.fetch.bind(globalThis))(`${n}manifest.json`, {
    cache: "no-cache",
    credentials: "same-origin",
    headers: { Accept: "application/json" }
  }).then((a) => {
    if (!a.ok)
      throw new Error(`GET ${n}manifest.json -> HTTP ${a.status}`);
    return a.json();
  }).then((a) => j(a)).catch((a) => (t.manifests.delete(n), console.warn("[shared-assets] manifest unavailable, using an empty one:", a), A));
  return t.manifests.set(n, u), u;
}
function y(e) {
  return typeof e == "object" && e !== null && !Array.isArray(e);
}
function S(e, n) {
  const t = {};
  if (e === void 0)
    return t;
  if (!y(e))
    throw new Error(`manifest.${n} must be an object`);
  for (const [o, r] of Object.entries(e))
    y(r) && typeof r.path == "string" && r.path.length > 0 ? t[o] = { path: r.path, label: typeof r.label == "string" ? r.label : void 0 } : console.warn(`[shared-assets] ignoring manifest.${n}.${o}: missing "path"`);
  return t;
}
function w(e) {
  return Array.isArray(e) ? e.filter((n) => typeof n == "string") : void 0;
}
function j(e) {
  if (!y(e))
    throw new Error("manifest.json must contain a JSON object");
  if (e.schemaVersion !== 1)
    throw new Error(`unsupported schemaVersion ${String(e.schemaVersion)} (expected 1)`);
  const n = S(e.icons, "icons"), t = S(e.images, "images"), o = [];
  if (Array.isArray(e.nodeIconRules))
    for (const a of e.nodeIconRules) {
      if (!y(a) || typeof a.icon != "string" || !y(a.match)) {
        console.warn("[shared-assets] ignoring malformed rule", a);
        continue;
      }
      const c = a.match;
      o.push({
        icon: a.icon,
        match: {
          categories: w(c.categories),
          sysObjectIdPrefixes: w(c.sysObjectIdPrefixes),
          foreignSources: w(c.foreignSources),
          labelPattern: typeof c.labelPattern == "string" ? c.labelPattern : void 0
        }
      });
    }
  const r = typeof e.revision == "number" || typeof e.revision == "string" ? e.revision : "", u = typeof e.defaultIcon == "string" ? e.defaultIcon : "unknown";
  return { schemaVersion: 1, revision: r, icons: n, images: t, nodeIconRules: o, defaultIcon: u };
}
function R(e) {
  const n = /* @__PURE__ */ new Set();
  for (const t of e.categories ?? []) {
    const o = typeof t == "string" ? t : t?.name;
    o && n.add(o.toLowerCase());
  }
  return n;
}
function V(e) {
  if (!e)
    return "";
  const n = e.trim();
  return n.startsWith(".") ? n : `.${n}`;
}
function x(e, n) {
  const t = V(e), o = V(n);
  return t !== "" && o !== "" && (t === o || t.startsWith(`${o}.`));
}
function U(e, n) {
  let t = !1;
  if (n.categories && n.categories.length > 0) {
    t = !0;
    const o = R(e);
    if (!n.categories.some((r) => o.has(r.toLowerCase())))
      return !1;
  }
  if (n.sysObjectIdPrefixes && n.sysObjectIdPrefixes.length > 0 && (t = !0, !n.sysObjectIdPrefixes.some((o) => x(e.sysObjectId, o))) || n.foreignSources && n.foreignSources.length > 0 && (t = !0, !e.foreignSource || !n.foreignSources.includes(e.foreignSource)))
    return !1;
  if (n.labelPattern) {
    t = !0;
    let o;
    try {
      o = new RegExp(n.labelPattern, "i");
    } catch {
      return !1;
    }
    if (!e.label || !o.test(e.label))
      return !1;
  }
  return t;
}
function N(e, n) {
  for (const t of n.nodeIconRules)
    if (U(e, t.match))
      return t.icon;
  return n.defaultIcon;
}
function O(e, n, t = p) {
  const o = n.icons[e], r = o ? o.path : `icons/${e}.svg`;
  return $(r, { base: t, revision: n.revision });
}
function C(e, n, t = p) {
  const o = n.images?.[e];
  return o ? $(o.path, { base: t, revision: n.revision }) : void 0;
}
function L(e, n, t = p) {
  return O(N(e, n), n, t);
}
function B(e, n = p) {
  return O(e.defaultIcon, e, n);
}
const M = window.Vue.defineComponent, f = window.Vue.openBlock, h = window.Vue.createElementBlock, F = window.Vue.createCommentVNode, s = window.Vue.createElementVNode, K = window.Vue.unref, m = window.Vue.toDisplayString, _ = window.Vue.createTextVNode, D = window.Vue.renderList, z = window.Vue.Fragment, G = window.Vue.pushScopeId, H = window.Vue.popScopeId, v = (e) => (G("data-v-15a17394"), e = e(), H(), e), W = { class: "lab-ni" }, q = { class: "lab-ni__header" }, Y = ["src"], J = /* @__PURE__ */ v(() => /* @__PURE__ */ s("h1", { class: "lab-ni__title" }, "Node Inventory", -1)), Q = { class: "lab-ni__muted" }, X = { key: 0 }, Z = {
  key: 1,
  class: "lab-ni__error"
}, ee = {
  key: 2,
  class: "lab-ni__muted"
}, ne = /* @__PURE__ */ v(() => /* @__PURE__ */ s("code", null, "scripts/provision-demo-nodes.sh", -1)), te = {
  key: 3,
  class: "lab-ni__table"
}, oe = /* @__PURE__ */ v(() => /* @__PURE__ */ s("thead", null, [
  /* @__PURE__ */ s("tr", null, [
    /* @__PURE__ */ s("th", null, "Icon"),
    /* @__PURE__ */ s("th", null, "Node"),
    /* @__PURE__ */ s("th", null, "Categories"),
    /* @__PURE__ */ s("th", null, "sysObjectID"),
    /* @__PURE__ */ s("th", null, "Requisition"),
    /* @__PURE__ */ s("th", null, "Icon key")
  ])
], -1)), se = ["src", "alt"], E = window.Vue.computed, re = window.Vue.onMounted, b = window.Vue.ref, ie = /* @__PURE__ */ M({
  __name: "NodeInventory",
  setup(e) {
    const n = b(A), t = b([]), o = b(!0), r = b("");
    async function u() {
      const i = await fetch("/opennms/api/v2/nodes?limit=500&offset=0&orderBy=label", {
        headers: { Accept: "application/json" },
        credentials: "same-origin"
      });
      if (i.status === 204)
        return [];
      if (!i.ok)
        throw new Error(`GET /opennms/api/v2/nodes -> HTTP ${i.status}`);
      return (await i.json()).node ?? [];
    }
    re(async () => {
      try {
        const [i, l] = await Promise.all([P(), u()]);
        n.value = i, t.value = l;
      } catch (i) {
        r.value = i instanceof Error ? i.message : String(i);
      } finally {
        o.value = !1;
      }
    });
    const a = E(() => C("lab-banner", n.value)), c = E(
      () => t.value.map((i) => ({
        id: String(i.id),
        label: i.label,
        categories: (i.categories ?? []).map((l) => l.name).join(", "),
        sysObjectId: i.sysObjectId ?? "",
        foreignSource: i.foreignSource ?? "",
        iconKey: N(i, n.value),
        iconUrl: L(i, n.value)
      }))
    );
    function g(i) {
      const l = i.target;
      if (l.dataset.fallback === "1") {
        l.style.visibility = "hidden";
        return;
      }
      l.dataset.fallback = "1", l.src = B(n.value);
    }
    return (i, l) => (f(), h("div", W, [
      s("header", q, [
        a.value ? (f(), h("img", {
          key: 0,
          src: a.value,
          class: "lab-ni__banner",
          alt: "Shared Assets Lab",
          width: "240",
          height: "48",
          "data-shared-asset": "banner"
        }, null, 8, Y)) : F("", !0),
        s("div", null, [
          J,
          s("p", Q, [
            _(" Icons are loaded from "),
            s("code", null, m(K(p)), 1),
            _(" (manifest revision "),
            s("code", null, m(n.value.revision === "" ? "n/a" : n.value.revision), 1),
            _("). The Icon Catalog plugin uses the very same files. ")
          ])
        ])
      ]),
      o.value ? (f(), h("p", X, "Loading nodes...")) : r.value ? (f(), h("p", Z, m(r.value), 1)) : c.value.length === 0 ? (f(), h("p", ee, [
        _(" No nodes yet. Run "),
        ne,
        _(" to import a few demo nodes. ")
      ])) : (f(), h("table", te, [
        oe,
        s("tbody", null, [
          (f(!0), h(z, null, D(c.value, (d) => (f(), h("tr", {
            key: d.id
          }, [
            s("td", null, [
              s("img", {
                src: d.iconUrl,
                alt: d.iconKey,
                width: "32",
                height: "32",
                "data-shared-asset": "node-icon",
                onError: g
              }, null, 40, se)
            ]),
            s("td", null, m(d.label), 1),
            s("td", null, m(d.categories), 1),
            s("td", null, [
              s("code", null, m(d.sysObjectId), 1)
            ]),
            s("td", null, m(d.foreignSource), 1),
            s("td", null, [
              s("code", null, m(d.iconKey), 1)
            ])
          ]))), 128))
        ])
      ]))
    ]));
  }
}), ae = (e, n) => {
  const t = e.__vccOpts || e;
  for (const [o, r] of n)
    t[o] = r;
  return t;
}, ce = /* @__PURE__ */ ae(ie, [["__scopeId", "data-v-15a17394"]]);
window.labNodeInventory = ce;
