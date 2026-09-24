/**
 * Where Jetty serves the shared folder. The container bind-mounts the host
 * folder at /usr/share/opennms/jetty-webapps/opennms/assets/shared, and the
 * "opennms" webapp (context path /opennms) serves it with its DefaultServlet.
 *
 * The OpenNMS UI itself hard-codes /opennms/rest and /opennms/api/v2 at build
 * time, so hard-coding /opennms here is no less portable than the host UI.
 */
export const DEFAULT_BASE = '/opennms/assets/shared/'

export function normalizeBase(base: string): string {
  return base.endsWith('/') ? base : `${base}/`
}

export interface AssetUrlOptions {
  /** Override the base URL (for example when testing against another server). */
  base?: string
  /** Cache-busting token, usually the manifest revision. */
  revision?: number | string
}

/**
 * Build the URL of a file in the shared folder.
 *
 *   assetUrl('icons/router.svg', { revision: 3 })
 *   // -> '/opennms/assets/shared/icons/router.svg?rev=3'
 *
 * Each path segment is URL-encoded. Empty, "." and ".." segments are rejected so
 * a manifest entry can never point outside the shared folder.
 */
export function assetUrl(relativePath: string, options: AssetUrlOptions = {}): string {
  const base = normalizeBase(options.base ?? DEFAULT_BASE)
  const trimmed = relativePath.replace(/^\/+/, '')
  const segments = trimmed.split('/')
  if (trimmed === '' || segments.some((s) => s === '' || s === '.' || s === '..')) {
    throw new Error(`Invalid shared asset path: "${relativePath}"`)
  }
  const encoded = segments.map((s) => encodeURIComponent(s)).join('/')
  const hasRevision = options.revision !== undefined && options.revision !== null && `${options.revision}` !== ''
  const query = hasRevision ? `?rev=${encodeURIComponent(String(options.revision))}` : ''
  return `${base}${encoded}${query}`
}
