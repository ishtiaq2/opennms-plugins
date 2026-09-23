import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  assetUrl,
  clearManifestCache,
  EMPTY_MANIFEST,
  iconUrl,
  imageUrl,
  loadManifest,
  nodeIconUrl,
  oidHasPrefix,
  parseManifest,
  resolveIconKey
} from '../src/index'

// The real catalog shipped in this repo, so the tests also guard the rules in it.
const manifestPath = fileURLToPath(new URL('../../../shared-assets/manifest.json', import.meta.url))
const rawManifest = JSON.parse(readFileSync(manifestPath, 'utf8'))
const manifest = parseManifest(rawManifest)

const okResponse = (body: unknown) =>
  new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } })

afterEach(() => {
  clearManifestCache()
  vi.restoreAllMocks()
})

describe('assetUrl', () => {
  it('builds URLs under /opennms/assets/shared/', () => {
    expect(assetUrl('icons/router.svg')).toBe('/opennms/assets/shared/icons/router.svg')
  })
  it('appends the revision for cache busting', () => {
    expect(assetUrl('icons/router.svg', { revision: 7 })).toBe('/opennms/assets/shared/icons/router.svg?rev=7')
  })
  it('accepts a base without trailing slash and trims leading slashes', () => {
    expect(assetUrl('/icons/a.svg', { base: 'http://nms:8980/opennms/assets/shared' })).toBe(
      'http://nms:8980/opennms/assets/shared/icons/a.svg'
    )
  })
  it('encodes each segment', () => {
    expect(assetUrl('icons/core switch #1.svg')).toBe('/opennms/assets/shared/icons/core%20switch%20%231.svg')
  })
  it.each(['../etc/passwd', 'icons/../../x', 'icons//a.svg', './a.svg', ''])('rejects %j', (p) => {
    expect(() => assetUrl(p)).toThrow(/Invalid shared asset path/)
  })
})

describe('oidHasPrefix', () => {
  it('matches on arc boundaries only', () => {
    expect(oidHasPrefix('.1.3.6.1.4.1.9.1.1208', '.1.3.6.1.4.1.9')).toBe(true)
    expect(oidHasPrefix('.1.3.6.1.4.1.99.1', '.1.3.6.1.4.1.9')).toBe(false)
    expect(oidHasPrefix('1.3.6.1.4.1.8072.3.2.10', '.1.3.6.1.4.1.8072.3.2.10')).toBe(true)
    expect(oidHasPrefix(null, '.1.3')).toBe(false)
  })
})

describe('resolveIconKey with the shipped manifest.json', () => {
  it.each([
    [{ categories: [{ name: 'Routers' }] }, 'router'],
    [{ categories: ['switches'] }, 'switch'],
    [{ categories: [{ name: 'Firewalls' }] }, 'firewall'],
    [{ label: 'raspberry-lab', sysObjectId: '.1.3.6.1.4.1.8072.3.2.10' }, 'sbc'],
    [{ label: 'pi-01' }, 'sbc'],
    [{ label: 'spider' }, 'unknown'],
    [{ label: 'web01', sysObjectId: '.1.3.6.1.4.1.8072.3.2.10', categories: [{ name: 'Servers' }] }, 'linux'],
    [{ label: 'db01', categories: [{ name: 'Servers' }] }, 'server'],
    [{ label: 'x', sysObjectId: '.1.3.6.1.4.1.8072.3.2.100' }, 'unknown'],
    [{}, 'unknown']
  ])('%j -> %s', (node, expected) => {
    expect(resolveIconKey(node, manifest)).toBe(expected)
  })

  it('every rule and the default point at an icon that exists in the manifest', () => {
    for (const rule of manifest.nodeIconRules) {
      expect(manifest.icons[rule.icon], rule.icon).toBeDefined()
    }
    expect(manifest.icons[manifest.defaultIcon]).toBeDefined()
  })
})

describe('iconUrl / imageUrl / nodeIconUrl', () => {
  it('uses the manifest path and revision', () => {
    expect(iconUrl('router', manifest)).toBe(`/opennms/assets/shared/icons/router.svg?rev=${manifest.revision}`)
  })
  it('falls back to the icons/<key>.svg convention for unknown keys', () => {
    expect(iconUrl('load-balancer', manifest)).toBe(
      `/opennms/assets/shared/icons/load-balancer.svg?rev=${manifest.revision}`
    )
  })
  it('resolves named images', () => {
    expect(imageUrl('lab-banner', manifest)).toMatch(/\/branding\/lab-banner\.png\?rev=/)
    expect(imageUrl('nope', manifest)).toBeUndefined()
  })
  it('combines rule resolution and URL building', () => {
    expect(nodeIconUrl({ categories: ['Routers'] }, manifest)).toMatch(/icons\/router\.svg/)
  })
})

describe('parseManifest', () => {
  it('rejects unknown schema versions', () => {
    expect(() => parseManifest({ ...rawManifest, schemaVersion: 2 })).toThrow(/schemaVersion/)
  })
  it('drops malformed rules and icons but keeps the rest', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const m = parseManifest({
      schemaVersion: 1,
      revision: 3,
      icons: { ok: { path: 'icons/ok.svg' }, broken: { label: 'no path' } },
      nodeIconRules: [{ icon: 'ok', match: { categories: ['A'] } }, { match: {} }, 'junk'],
      defaultIcon: 'ok'
    })
    expect(Object.keys(m.icons)).toEqual(['ok'])
    expect(m.nodeIconRules).toHaveLength(1)
    expect(warn).toHaveBeenCalled()
  })
})

describe('loadManifest', () => {
  it('fetches once per page even when several plugins ask', async () => {
    const fetchImpl = vi.fn(async () => okResponse(rawManifest))
    const [a, b] = await Promise.all([loadManifest({ fetchImpl }), loadManifest({ fetchImpl })])
    expect(a).toBe(b)
    expect(fetchImpl).toHaveBeenCalledTimes(1)
    expect(fetchImpl).toHaveBeenCalledWith('/opennms/assets/shared/manifest.json', expect.objectContaining({ cache: 'no-cache' }))
  })

  it('shares the cache between separately bundled copies of the helper', async () => {
    const fetchImpl = vi.fn(async () => okResponse(rawManifest))
    await loadManifest({ fetchImpl })
    vi.resetModules() // simulate a second plugin with its own copy of this module
    const copy = await import('../src/manifest')
    await copy.loadManifest({ fetchImpl })
    expect(fetchImpl).toHaveBeenCalledTimes(1)
  })

  it('falls back to an empty manifest on HTTP errors and retries next time', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(new Response('nope', { status: 404 }))
      .mockResolvedValueOnce(okResponse(rawManifest))
    expect(await loadManifest({ fetchImpl })).toBe(EMPTY_MANIFEST)
    const second = await loadManifest({ fetchImpl })
    expect(second.revision).toBe(rawManifest.revision)
    expect(fetchImpl).toHaveBeenCalledTimes(2)
  })

  it('refetches when forced', async () => {
    const fetchImpl = vi.fn(async () => okResponse(rawManifest))
    await loadManifest({ fetchImpl })
    await loadManifest({ fetchImpl, force: true })
    expect(fetchImpl).toHaveBeenCalledTimes(2)
  })
})
