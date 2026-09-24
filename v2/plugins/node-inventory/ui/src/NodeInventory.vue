<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  DEFAULT_BASE,
  EMPTY_MANIFEST,
  defaultIconUrl,
  imageUrl,
  loadManifest,
  nodeIconUrl,
  resolveIconKey,
  type SharedAssetsManifest
} from '@onms-lab/shared-assets'

/** The fields this page shows, as returned by GET /opennms/api/v2/nodes. */
interface OnmsNode {
  id: string | number
  label: string
  foreignSource?: string | null
  sysObjectId?: string | null
  categories?: Array<{ name: string }>
}

const manifest = ref<SharedAssetsManifest>(EMPTY_MANIFEST)
const nodes = ref<OnmsNode[]>([])
const loading = ref(true)
const error = ref('')

async function fetchNodes(): Promise<OnmsNode[]> {
  // Same endpoint and parameters the OpenNMS UI's own node list uses. The browser sends the
  // JSESSIONID cookie of the logged-in user, which Spring Security accepts for /api/v2/**.
  const resp = await fetch('/opennms/api/v2/nodes?limit=500&offset=0&orderBy=label', {
    headers: { Accept: 'application/json' },
    credentials: 'same-origin'
  })
  if (resp.status === 204) {
    return [] // v2 answers 204 No Content when there are no nodes
  }
  if (!resp.ok) {
    throw new Error(`GET /opennms/api/v2/nodes -> HTTP ${resp.status}`)
  }
  const body = (await resp.json()) as { node?: OnmsNode[] }
  return body.node ?? []
}

onMounted(async () => {
  try {
    // loadManifest() is shared page-wide: if the Icon Catalog plugin already fetched it, this is free.
    const [m, n] = await Promise.all([loadManifest(), fetchNodes()])
    manifest.value = m
    nodes.value = n
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
})

const bannerUrl = computed(() => imageUrl('lab-banner', manifest.value))

const rows = computed(() =>
  nodes.value.map((node) => ({
    id: String(node.id),
    label: node.label,
    categories: (node.categories ?? []).map((c) => c.name).join(', '),
    sysObjectId: node.sysObjectId ?? '',
    foreignSource: node.foreignSource ?? '',
    iconKey: resolveIconKey(node, manifest.value),
    iconUrl: nodeIconUrl(node, manifest.value)
  }))
)

/** A rule may point at a file that is not there (yet). Show the default icon instead, once. */
function onIconError(event: Event) {
  const img = event.target as HTMLImageElement
  if (img.dataset.fallback === '1') {
    img.style.visibility = 'hidden'
    return
  }
  img.dataset.fallback = '1'
  img.src = defaultIconUrl(manifest.value)
}
</script>

<template>
  <div class="lab-ni">
    <header class="lab-ni__header">
      <img
        v-if="bannerUrl"
        :src="bannerUrl"
        class="lab-ni__banner"
        alt="Shared Assets Lab"
        width="240"
        height="48"
        data-shared-asset="banner"
      />
      <div>
        <h1 class="lab-ni__title">Node Inventory</h1>
        <p class="lab-ni__muted">
          Icons are loaded from <code>{{ DEFAULT_BASE }}</code> (manifest revision
          <code>{{ manifest.revision === '' ? 'n/a' : manifest.revision }}</code>). The Icon Catalog plugin uses
          the very same files.
        </p>
      </div>
    </header>

    <p v-if="loading">Loading nodes...</p>
    <p v-else-if="error" class="lab-ni__error">{{ error }}</p>
    <p v-else-if="rows.length === 0" class="lab-ni__muted">
      No nodes yet. Run <code>scripts/provision-demo-nodes.sh</code> to import a few demo nodes.
    </p>

    <table v-else class="lab-ni__table">
      <thead>
        <tr>
          <th>Icon</th>
          <th>Node</th>
          <th>Categories</th>
          <th>sysObjectID</th>
          <th>Requisition</th>
          <th>Icon key</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td>
            <img
              :src="row.iconUrl"
              :alt="row.iconKey"
              width="32"
              height="32"
              data-shared-asset="node-icon"
              @error="onIconError"
            />
          </td>
          <td>{{ row.label }}</td>
          <td>{{ row.categories }}</td>
          <td><code>{{ row.sysObjectId }}</code></td>
          <td>{{ row.foreignSource }}</td>
          <td><code>{{ row.iconKey }}</code></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.lab-ni {
  padding: 1.5rem;
  font-family: inherit;
}
.lab-ni__header {
  display: flex;
  gap: 1.25rem;
  align-items: center;
  margin-bottom: 1.25rem;
}
.lab-ni__banner {
  border-radius: 8px;
}
.lab-ni__title {
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
}
.lab-ni__muted {
  margin: 0;
  opacity: 0.75;
}
.lab-ni__error {
  color: #b91c1c;
}
.lab-ni__table {
  border-collapse: collapse;
  width: 100%;
}
.lab-ni__table th,
.lab-ni__table td {
  text-align: left;
  padding: 0.4rem 0.75rem;
  border-bottom: 1px solid rgba(127, 127, 127, 0.25);
  vertical-align: middle;
}
</style>
