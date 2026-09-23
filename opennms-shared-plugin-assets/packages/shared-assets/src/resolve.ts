import type { MatchCriteria, NodeLike, SharedAssetsManifest } from './types'
import { assetUrl, DEFAULT_BASE } from './url'

function categoryNames(node: NodeLike): Set<string> {
  const names = new Set<string>()
  for (const c of node.categories ?? []) {
    const name = typeof c === 'string' ? c : c?.name
    if (name) {
      names.add(name.toLowerCase())
    }
  }
  return names
}

function normalizeOid(oid: string | null | undefined): string {
  if (!oid) {
    return ''
  }
  const trimmed = oid.trim()
  return trimmed.startsWith('.') ? trimmed : `.${trimmed}`
}

/** True when oid equals prefix or continues it at an arc boundary (.1.3.6.1.4.1.9 does not match .1.3.6.1.4.1.99). */
export function oidHasPrefix(oid: string | null | undefined, prefix: string): boolean {
  const o = normalizeOid(oid)
  const p = normalizeOid(prefix)
  return o !== '' && p !== '' && (o === p || o.startsWith(`${p}.`))
}

/** All conditions present must match. A rule without any condition never matches. */
export function matches(node: NodeLike, criteria: MatchCriteria): boolean {
  let tested = false
  if (criteria.categories && criteria.categories.length > 0) {
    tested = true
    const names = categoryNames(node)
    if (!criteria.categories.some((c) => names.has(c.toLowerCase()))) {
      return false
    }
  }
  if (criteria.sysObjectIdPrefixes && criteria.sysObjectIdPrefixes.length > 0) {
    tested = true
    if (!criteria.sysObjectIdPrefixes.some((p) => oidHasPrefix(node.sysObjectId, p))) {
      return false
    }
  }
  if (criteria.foreignSources && criteria.foreignSources.length > 0) {
    tested = true
    if (!node.foreignSource || !criteria.foreignSources.includes(node.foreignSource)) {
      return false
    }
  }
  if (criteria.labelPattern) {
    tested = true
    let re: RegExp
    try {
      re = new RegExp(criteria.labelPattern, 'i')
    } catch {
      return false
    }
    if (!node.label || !re.test(node.label)) {
      return false
    }
  }
  return tested
}

/** Icon key for a node: the first matching rule, else the manifest's defaultIcon. */
export function resolveIconKey(node: NodeLike, manifest: SharedAssetsManifest): string {
  for (const rule of manifest.nodeIconRules) {
    if (matches(node, rule.match)) {
      return rule.icon
    }
  }
  return manifest.defaultIcon
}

/**
 * URL of an icon by key. Keys missing from the manifest fall back to the naming
 * convention icons/<key>.svg, so a file dropped into the folder is usable by key
 * even before anyone edits manifest.json.
 */
export function iconUrl(key: string, manifest: SharedAssetsManifest, base: string = DEFAULT_BASE): string {
  const entry = manifest.icons[key]
  const path = entry ? entry.path : `icons/${key}.svg`
  return assetUrl(path, { base, revision: manifest.revision })
}

/** URL of a named non-icon image (manifest "images" section), or undefined. */
export function imageUrl(key: string, manifest: SharedAssetsManifest, base: string = DEFAULT_BASE): string | undefined {
  const entry = manifest.images?.[key]
  return entry ? assetUrl(entry.path, { base, revision: manifest.revision }) : undefined
}

export function nodeIconUrl(node: NodeLike, manifest: SharedAssetsManifest, base: string = DEFAULT_BASE): string {
  return iconUrl(resolveIconKey(node, manifest), manifest, base)
}

export function defaultIconUrl(manifest: SharedAssetsManifest, base: string = DEFAULT_BASE): string {
  return iconUrl(manifest.defaultIcon, manifest, base)
}
