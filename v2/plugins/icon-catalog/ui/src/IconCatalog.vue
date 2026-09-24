<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  DEFAULT_BASE,
  EMPTY_MANIFEST,
  assetUrl,
  loadManifest,
  type SharedAssetsManifest
} from '@onms-lab/shared-assets'

/** What Jetty answered for one URL. Shown so you can see how the files are served. */
interface HeadInfo {
  status: number
  contentType: string
  cacheControl: string
  lastModified: string
}

interface CatalogItem {
  key: string
  kind: 'icon' | 'image'
  label: string
  path: string
  url: string
  head?: HeadInfo
}

const manifest = ref<SharedAssetsManifest>(EMPTY_MANIFEST)
const items = ref<CatalogItem[]>([])
const loading = ref(true)

const probePath = ref('icons/')
const probeResult = ref<HeadInfo | null>(null)
const probeUrl = ref('')
const probeError = ref('')

async function head(url: string): Promise<HeadInfo> {
  // cache: 'no-store' so the table shows what Jetty sends right now, not the browser cache.
  const resp = await fetch(url, { method: 'HEAD', cache: 'no-store', credentials: 'same-origin' })
  return {
    status: resp.status,
    contentType: resp.headers.get('content-type') ?? '-',
    cacheControl: resp.headers.get('cache-control') ?? '-',
    lastModified: resp.headers.get('last-modified') ?? '-'
  }
}

onMounted(async () => {
  const m = await loadManifest()
  manifest.value = m
  const list: CatalogItem[] = []
  for (const [key, entry] of Object.entries(m.icons)) {
    list.push({ key, kind: 'icon', label: entry.label ?? key, path: entry.path, url: assetUrl(entry.path, { revision: m.revision }) })
  }
  for (const [key, entry] of Object.entries(m.images ?? {})) {
    list.push({ key, kind: 'image', label: entry.label ?? key, path: entry.path, url: assetUrl(entry.path, { revision: m.revision }) })
  }
  items.value = list
  loading.value = false
  await Promise.all(
    list.map(async (item) => {
      try {
        item.head = await head(item.url)
      } catch {
        item.head = { status: 0, contentType: 'network error', cacheControl: '-', lastModified: '-' }
      }
    })
  )
  items.value = [...list]
})

async function probe() {
  probeError.value = ''
  probeResult.value = null
  probeUrl.value = ''
  try {
    const url = assetUrl(probePath.value)
    probeResult.value = await head(url)
    probeUrl.value = url
  } catch (e) {
    probeError.value = e instanceof Error ? e.message : String(e)
  }
}

const probeIsImage = computed(
  () => probeResult.value !== null && probeResult.value.status === 200 && probeResult.value.contentType.startsWith('image/')
)
</script>

<template>
  <div class="lab-ic">
    <h1 class="lab-ic__title">Shared Icon Catalog</h1>
    <p class="lab-ic__muted">
      Every entry of <code>manifest.json</code> (revision <code>{{ manifest.revision === '' ? 'n/a' : manifest.revision }}</code>),
      served by Jetty from <code>{{ DEFAULT_BASE }}</code>. The Node Inventory plugin renders the same files.
    </p>

    <p v-if="loading">Loading manifest...</p>
    <div v-else class="lab-ic__grid">
      <figure v-for="item in items" :key="item.kind + ':' + item.key" class="lab-ic__card">
        <img
          :src="item.url"
          :alt="item.label"
          :class="item.kind === 'image' ? 'lab-ic__wide' : ''"
          :width="item.kind === 'image' ? 240 : 64"
          :height="item.kind === 'image' ? 48 : 64"
          data-shared-asset="catalog"
        />
        <figcaption>
          <strong>{{ item.key }}</strong>
          <span>{{ item.label }}</span>
          <code>{{ item.path }}</code>
          <small v-if="item.head">
            HTTP {{ item.head.status }} | {{ item.head.contentType }}<br />
            Cache-Control: {{ item.head.cacheControl }}
          </small>
        </figcaption>
      </figure>
    </div>

    <section class="lab-ic__section">
      <h2>Probe a path</h2>
      <p class="lab-ic__muted">
        Copy a file into the host folder <code>shared-assets/</code>, type its path and press Check.
        Jetty serves it on the next request: no restart, no rebuild, no manifest edit needed for a direct URL.
      </p>
      <form class="lab-ic__probe" @submit.prevent="probe">
        <input v-model="probePath" placeholder="icons/my-new-icon.svg" aria-label="Path relative to the shared folder" />
        <button type="submit">Check</button>
      </form>
      <p v-if="probeError" class="lab-ic__error">{{ probeError }}</p>
      <p v-if="probeResult">
        <code>{{ probeUrl }}</code> -> HTTP {{ probeResult.status }} | {{ probeResult.contentType }} | Last-Modified:
        {{ probeResult.lastModified }}
      </p>
      <img v-if="probeIsImage" :src="probeUrl" alt="probe result" width="64" height="64" data-shared-asset="probe" />
    </section>

    <section class="lab-ic__section">
      <h2>Node icon rules</h2>
      <p class="lab-ic__muted">Evaluated top to bottom; the first match wins. Default icon: <code>{{ manifest.defaultIcon }}</code>.</p>
      <table class="lab-ic__table">
        <thead>
          <tr><th>#</th><th>Icon</th><th>When</th></tr>
        </thead>
        <tbody>
          <tr v-for="(rule, i) in manifest.nodeIconRules" :key="i">
            <td>{{ i + 1 }}</td>
            <td><code>{{ rule.icon }}</code></td>
            <td><code>{{ JSON.stringify(rule.match) }}</code></td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.lab-ic {
  padding: 1.5rem;
}
.lab-ic__title {
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
}
.lab-ic__muted {
  opacity: 0.75;
}
.lab-ic__error {
  color: #b91c1c;
}
.lab-ic__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}
.lab-ic__card {
  margin: 0;
  padding: 0.75rem;
  border: 1px solid rgba(127, 127, 127, 0.3);
  border-radius: 10px;
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  flex-wrap: wrap;
}
.lab-ic__card figcaption {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
  overflow-wrap: anywhere;
}
.lab-ic__wide {
  border-radius: 8px;
  max-width: 100%;
  height: auto;
}
.lab-ic__section {
  margin-top: 2rem;
}
.lab-ic__probe {
  display: flex;
  gap: 0.5rem;
}
.lab-ic__probe input {
  min-width: 18rem;
  padding: 0.3rem 0.5rem;
}
.lab-ic__table {
  border-collapse: collapse;
}
.lab-ic__table th,
.lab-ic__table td {
  text-align: left;
  padding: 0.3rem 0.75rem;
  border-bottom: 1px solid rgba(127, 127, 127, 0.25);
}
</style>
