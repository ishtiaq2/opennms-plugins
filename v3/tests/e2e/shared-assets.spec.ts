import { expect, test, type Page } from '@playwright/test'

// Runs against the lab (compose.yml) after scripts/build-plugins.sh deployed both KARs and
// scripts/provision-demo-nodes.sh imported the demo nodes.
//   cd tests/e2e && npm install && npm run install-browser && npm test
// ONMS_URL (http://localhost:8980), ONMS_USER / ONMS_PASS (admin / admin).
// ONMS_UI_ENTRY lets the same test run against a stand-in host page (default /opennms/ui/).
const UI = process.env.ONMS_UI_ENTRY ?? '/opennms/ui/'
const NODE_INVENTORY = `${UI}#/plugins/labNodeInventory/node-inventory/nodeInventory.es.js`
const ICON_CATALOG = `${UI}#/plugins/labIconCatalog/icon-catalog/iconCatalog.es.js`

async function login(page: Page) {
  if (process.env.ONMS_SKIP_LOGIN === '1') return
  await page.goto('/opennms/login.jsp')
  await page.fill('#input_j_username', process.env.ONMS_USER ?? 'admin')
  await page.fill('#input_j_password', process.env.ONMS_PASS ?? 'admin')
  await Promise.all([page.waitForURL((u) => !u.pathname.endsWith('login.jsp')), page.click('button[name="Login"]')])
}

/** Wait until every matching <img> finished loading, then return what the browser decoded. */
async function decodedImages(page: Page, selector: string) {
  await page.waitForFunction(
    (sel) => {
      const imgs = [...document.querySelectorAll<HTMLImageElement>(sel)]
      return imgs.length > 0 && imgs.every((i) => i.complete)
    },
    selector,
    { timeout: 20_000 }
  )
  return page.$$eval(selector, (imgs) =>
    (imgs as HTMLImageElement[]).map((i) => ({ src: i.getAttribute('src') ?? '', width: i.naturalWidth }))
  )
}

test('both plugins render the same shared icons, served by Jetty from /opennms/assets/shared/', async ({ page }) => {
  const cspViolations: string[] = []
  const manifestRequests: string[] = []
  page.on('console', (m) => {
    if (/Content Security Policy/i.test(m.text())) cspViolations.push(m.text())
  })
  page.on('request', (r) => {
    if (r.url().includes('/opennms/assets/shared/manifest.json')) manifestRequests.push(r.url())
  })

  await login(page)

  await page.goto(NODE_INVENTORY)
  await expect(page.locator('.lab-ni')).toBeVisible({ timeout: 30_000 })
  const inventory = await decodedImages(page, '.lab-ni img[data-shared-asset]')
  for (const img of inventory) {
    expect(img.src, 'served from the shared folder').toMatch(/^\/opennms\/assets\/shared\/.+\?rev=/)
    expect(img.width, `${img.src} decoded`).toBeGreaterThan(0)
  }

  // Same single-page app, second plugin: the manifest must not be fetched again.
  await page.evaluate((hash) => { location.hash = hash }, ICON_CATALOG.split('#')[1])
  await expect(page.locator('.lab-ic')).toBeVisible()
  const catalog = await decodedImages(page, '.lab-ic img[data-shared-asset="catalog"]')
  expect(catalog.length).toBeGreaterThan(0)
  for (const img of catalog) expect(img.width, `${img.src} decoded`).toBeGreaterThan(0)
  await expect(page.locator('.lab-ic__card small').first()).toContainText('max-age=3600')

  const shared = new Set(inventory.map((i) => i.src.split('?')[0]))
  const both = catalog.map((i) => i.src.split('?')[0]).filter((s) => shared.has(s))
  expect(both.length, 'the two plugins really use the same files').toBeGreaterThan(0)
  expect(manifestRequests.length, 'manifest.json fetched once for both plugins').toBe(1)
  // Only violations caused by the shared files or the two plugins count; the rest of the UI is not under test.
  const ours = cspViolations.filter((m) => /assets\/shared|ui-extension\/(module|css)\/lab/.test(m))
  if (cspViolations.length > ours.length) console.log('CSP messages from other parts of the UI:', cspViolations)
  expect(ours, 'no CSP violations caused by the shared assets or the plugins').toEqual([])
})

test('the shared folder is readable without a session (Spring Security permits /assets/**)', async ({ request }) => {
  const resp = await request.get('/opennms/assets/shared/manifest.json')
  expect(resp.status()).toBe(200)
  expect(resp.headers()['cache-control']).toContain('max-age=3600')
})
