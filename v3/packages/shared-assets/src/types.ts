/** One file in the shared-assets folder, addressed relative to its root. */
export interface AssetEntry {
  /** Relative path, e.g. "icons/router.svg". No leading slash, no "." or ".." segments. */
  path: string
  /** Human-readable name shown by plugins. */
  label?: string
}

/** Conditions of one node-icon rule. All conditions present must match (AND). */
export interface MatchCriteria {
  /** Any of these surveillance category names (case-insensitive). */
  categories?: string[]
  /** sysObjectID starts with one of these OIDs, on an arc boundary. */
  sysObjectIdPrefixes?: string[]
  /** Requisition (foreign source) name, exact match. */
  foreignSources?: string[]
  /** JavaScript regular expression tested case-insensitively against the node label. */
  labelPattern?: string
}

export interface NodeIconRule {
  /** A key of {@link SharedAssetsManifest.icons}. */
  icon: string
  match: MatchCriteria
}

/** Shape of shared-assets/manifest.json (see manifest.schema.json). */
export interface SharedAssetsManifest {
  schemaVersion: 1
  /** Bumped whenever an existing file changes; appended to URLs as ?rev=... */
  revision: number | string
  icons: Record<string, AssetEntry>
  images?: Record<string, AssetEntry>
  /** Evaluated top to bottom; first match wins. */
  nodeIconRules: NodeIconRule[]
  /** Icon key used when no rule matches. */
  defaultIcon: string
}

/**
 * The subset of an OpenNMS node that the rules look at. Both the v2 REST API
 * (/opennms/api/v2/nodes) and the v1 API return these fields.
 */
export interface NodeLike {
  label?: string | null
  sysObjectId?: string | null
  foreignSource?: string | null
  categories?: ReadonlyArray<{ name?: string | null } | string> | null
}
