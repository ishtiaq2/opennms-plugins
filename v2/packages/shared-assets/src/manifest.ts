import type { AssetEntry, NodeIconRule, SharedAssetsManifest } from './types'
import { DEFAULT_BASE, normalizeBase } from './url'

/** Returned when manifest.json is missing or invalid, so plugins still render. */
export const EMPTY_MANIFEST: SharedAssetsManifest = Object.freeze({
  schemaVersion: 1,
  revision: '',
  icons: {},
  images: {},
  nodeIconRules: [],
  defaultIcon: 'unknown'
}) as SharedAssetsManifest

/**
 * Several plugins run in the same page (the OpenNMS UI preloads every plugin
 * module at start-up). Each plugin bundles its own copy of this helper, so a
 * module-level cache would not be shared. The cache therefore lives on
 * globalThis: the first plugin that asks triggers the fetch, all others reuse it.
 */
const GLOBAL_KEY = '__onmsLabSharedAssets__'

interface Registry {
  manifests: Map<string, Promise<SharedAssetsManifest>>
}

function registry(): Registry {
  const g = globalThis as unknown as Record<string, Registry | undefined>
  let reg = g[GLOBAL_KEY]
  if (!reg) {
    reg = { manifests: new Map() }
    g[GLOBAL_KEY] = reg
  }
  return reg
}

export interface LoadManifestOptions {
  base?: string
  /** Ignore the page-wide cache and fetch again. */
  force?: boolean
  /** Injected in tests. Defaults to the browser's fetch. */
  fetchImpl?: typeof fetch
}

/**
 * Fetch and validate manifest.json once per page (per base URL).
 *
 * cache: 'no-cache' makes the browser revalidate with If-Modified-Since on every
 * page load. Jetty answers 304 when the file is unchanged, so this is cheap, and
 * it guarantees plugins see a new revision right after you edit the manifest.
 */
export function loadManifest(options: LoadManifestOptions = {}): Promise<SharedAssetsManifest> {
  const base = normalizeBase(options.base ?? DEFAULT_BASE)
  const reg = registry()
  const cached = options.force ? undefined : reg.manifests.get(base)
  if (cached) {
    return cached
  }
  const doFetch = options.fetchImpl ?? globalThis.fetch.bind(globalThis)
  const pending = doFetch(`${base}manifest.json`, {
    cache: 'no-cache',
    credentials: 'same-origin',
    headers: { Accept: 'application/json' }
  })
    .then((resp) => {
      if (!resp.ok) {
        throw new Error(`GET ${base}manifest.json -> HTTP ${resp.status}`)
      }
      return resp.json()
    })
    .then((json: unknown) => parseManifest(json))
    .catch((err: unknown) => {
      // Do not keep a failure in the cache: the next caller should try again.
      reg.manifests.delete(base)
      console.warn('[shared-assets] manifest unavailable, using an empty one:', err)
      return EMPTY_MANIFEST
    })
  reg.manifests.set(base, pending)
  return pending
}

/** Forget cached manifests (all bases). */
export function clearManifestCache(): void {
  registry().manifests.clear()
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

function parseAssetMap(v: unknown, what: string): Record<string, AssetEntry> {
  const out: Record<string, AssetEntry> = {}
  if (v === undefined) {
    return out
  }
  if (!isRecord(v)) {
    throw new Error(`manifest.${what} must be an object`)
  }
  for (const [key, entry] of Object.entries(v)) {
    if (isRecord(entry) && typeof entry.path === 'string' && entry.path.length > 0) {
      out[key] = { path: entry.path, label: typeof entry.label === 'string' ? entry.label : undefined }
    } else {
      console.warn(`[shared-assets] ignoring manifest.${what}.${key}: missing "path"`)
    }
  }
  return out
}

function stringArray(v: unknown): string[] | undefined {
  return Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string') : undefined
}

/** Validate the JSON loosely: bad entries are dropped with a warning instead of failing the page. */
export function parseManifest(json: unknown): SharedAssetsManifest {
  if (!isRecord(json)) {
    throw new Error('manifest.json must contain a JSON object')
  }
  if (json.schemaVersion !== 1) {
    throw new Error(`unsupported schemaVersion ${String(json.schemaVersion)} (expected 1)`)
  }
  const icons = parseAssetMap(json.icons, 'icons')
  const images = parseAssetMap(json.images, 'images')
  const rules: NodeIconRule[] = []
  if (Array.isArray(json.nodeIconRules)) {
    for (const raw of json.nodeIconRules) {
      if (!isRecord(raw) || typeof raw.icon !== 'string' || !isRecord(raw.match)) {
        console.warn('[shared-assets] ignoring malformed rule', raw)
        continue
      }
      const m = raw.match
      rules.push({
        icon: raw.icon,
        match: {
          categories: stringArray(m.categories),
          sysObjectIdPrefixes: stringArray(m.sysObjectIdPrefixes),
          foreignSources: stringArray(m.foreignSources),
          labelPattern: typeof m.labelPattern === 'string' ? m.labelPattern : undefined
        }
      })
    }
  }
  const revision = typeof json.revision === 'number' || typeof json.revision === 'string' ? json.revision : ''
  const defaultIcon = typeof json.defaultIcon === 'string' ? json.defaultIcon : 'unknown'
  return { schemaVersion: 1, revision, icons, images, nodeIconRules: rules, defaultIcon }
}
