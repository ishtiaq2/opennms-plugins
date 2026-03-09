#!/bin/bash
set -e
source ./_0_config.sh

UI_DIR="$PLUGIN_NAME/ui-extension"

echo "* Creating Advanced Vue 3 + TS UI structure in: $UI_DIR"

# Establish Directory Tree (Consolidated)
mkdir -p "$UI_DIR/src/router" \
         "$UI_DIR/src/views" \
         "$UI_DIR/src/stores" \
         "$UI_DIR/src/api" \
         "$UI_DIR/src/components/inventory/view/styles"

# 1. package.json
cat <<EOF > "$UI_DIR/package.json"
{
  "name": "ui-extension",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite --config vite.config.dev.mts",
    "build": "vue-tsc --noEmit && vite build",
    "type-check": "vue-tsc --noEmit"
  },
  "dependencies": {
    "vue": "3.5.18",
    "pinia": "3.0.3",
    "vue-router": "4.5.1",
    "axios": "^1.13.0",
    "bootstrap": "5.3.7",
    "bootstrap-vue-next": "0.30.4",
    "@fortawesome/fontawesome-svg-core": "6.5.0",
    "@fortawesome/free-solid-svg-icons": "6.5.0",
    "@fortawesome/vue-fontawesome": "3.0.5"
  },
  "devDependencies": {
    "vite": "^7.1.12",
    "typescript": "5.9.2",
    "vue-tsc": "3.0.5",
    "@vitejs/plugin-vue": "6.0.1",
    "vite-plugin-css-injected-by-js": "^3.5.2",
    "vite-plugin-externals": "0.6.2",
    "sass": "1.89.2",
    "@types/node": "20.19.9"
  }
}
EOF

# 2. tsconfig.json
cat <<EOF > "$UI_DIR/tsconfig.json"
{
  "compilerOptions": {
    "target": "esnext",
    "useDefineForClassFields": true,
    "module": "esnext",
    "moduleResolution": "node",
    "strict": true,
    "jsx": "preserve",
    "sourceMap": true,
    "resolveJsonModule": true,
    "esModuleInterop": true,
    "lib": ["esnext", "dom"],
    "skipLibCheck": true
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"]
}
EOF

# 3. vite.config.ts (Production)
cat <<EOF > "$UI_DIR/vite.config.ts"
import path from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteExternalsPlugin } from 'vite-plugin-externals'
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js'

export default defineConfig({
  plugins: [
    vue(),
    cssInjectedByJsPlugin(),
    viteExternalsPlugin({
      vue: 'Vue',
      pinia: 'Pinia',
      'vue-router': 'VueRouter'
    })
  ],
  build: {
    outDir: path.resolve(__dirname, '../plugin/src/main/resources/ui-ext'),
    emptyOutDir: true,
    cssCodeSplit: false,
    lib: {
      entry: path.resolve(__dirname, 'src/main.ts'),
      name: 'uiextension',
      fileName: () => \`uiextension.es.js\`,
      formats: ['es']
    }
  }
})
EOF

# 4. vite.config.dev.mts (Development Proxy)
cat <<EOF > "$UI_DIR/vite.config.dev.mts"
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/opennms/rest': {
        target: 'http://localhost:8980/',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
EOF

# 5. src/router/index.ts
cat <<EOF > "$UI_DIR/src/router/index.ts"
import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView }
  ]
})
export default router
EOF

# 6. src/views/HomeView.vue (UPDATED WITH TABLE)
cat <<EOF > "$UI_DIR/src/views/HomeView.vue"
<template>
  <div class="container mt-4">
    <div class="card shadow-sm">
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <h5 class="mb-0"><font-awesome-icon icon="home" /> Node Inventory: {{ config.user }}</h5>
        <button class="btn btn-sm btn-light" @click="nodeStore.fetchNodes" :disabled="nodeStore.loading">
          <font-awesome-icon :icon="nodeStore.loading ? 'coffee' : 'upload'" :spin="nodeStore.loading" /> 
          {{ nodeStore.loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
      <div class="card-body">
        <div v-if="nodeStore.loading && nodeStore.nodes.length === 0" class="text-center py-5">
          <font-awesome-icon icon="coffee" size="3x" spin class="text-secondary" />
          <p class="mt-3">Connecting to OpenNMS...</p>
        </div>

        <div v-else>
          <div class="table-responsive">
            <table class="table table-hover align-middle">
              <thead class="table-light">
                <tr>
                  <th>ID</th>
                  <th>Label</th>
                  <th>Foreign Source</th>
                  <th class="text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="node in nodeStore.nodes" :key="node.id">
                  <td><span class="badge bg-secondary">{{ node.id }}</span></td>
                  <td><strong>{{ node.label }}</strong></td>
                  <td><code class="text-muted">{{ node.foreignSource || 'None' }}</code></td>
                  <td class="text-center">
                    <font-awesome-icon icon="info-circle" class="text-success" />
                    <span class="ms-1 small">Provisioned</span>
                  </td>
                </tr>
                <tr v-if="nodeStore.nodes.length === 0">
                  <td colspan="4" class="text-center py-4 text-muted">No nodes found in this instance.</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="d-flex justify-content-between align-items-center mt-3">
             <small class="text-muted">Showing {{ nodeStore.nodes.length }} of {{ nodeStore.totalCount }} total nodes.</small>
             <span class="badge bg-info text-dark">OpenNMS API v1</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppConfig } from '../stores/appConfig'
import { useNodeStore } from '../stores/nodeStore'

const config = useAppConfig()
const nodeStore = useNodeStore()

onMounted(() => {
  nodeStore.fetchNodes()
})
</script>
EOF


# 7. src/stores/appConfig.ts
cat <<EOF > "$UI_DIR/src/stores/appConfig.ts"
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppConfig = defineStore('appConfig', () => {
  const user = ref('Guest')
  const baseUrl = ref('/opennms')
  const theme = ref('light')

  function setConfig(config: any) {
    if (config) {
      user.value = config.userName || 'Unknown'
      baseUrl.value = config.baseUrl || '/opennms'
      theme.value = config.theme || 'light'
    }
  }

  return { user, baseUrl, theme, setConfig }
})
EOF

# 8. src/main.ts
cat <<EOF > "$UI_DIR/src/main.ts"
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import { useAppConfig } from './stores/appConfig'
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { createBootstrap } from 'bootstrap-vue-next'

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css'
import "./components/inventory/view/styles/requisitions.scss"

import {
  faUser, faCoffee, faBars, faHome, faBook, faAddressBook,
  faBookReader, faArrowDown, faDirections, faExpand,
  faAngleDoubleDown, faAngleDoubleRight, faAngleRight, faAngleDown, faInfoCircle,
  faTimesCircle, faTriangleExclamation, faUpload
} from '@fortawesome/free-solid-svg-icons'

library.add(
  faUser, faCoffee, faBars, faHome, faBook, faAddressBook,
  faBookReader, faArrowDown, faDirections, faExpand,
  faAngleDoubleRight, faAngleDoubleDown, faAngleRight, faAngleDown, faInfoCircle,
  faTimesCircle, faTriangleExclamation, faUpload
)

// @ts-ignore
window['uiextension'] = App

export default function (container: HTMLElement, config: any) {
    const app = createApp(App)
    const pinia = createPinia()
    app.use(pinia)
    const store = useAppConfig(pinia)
    store.setConfig(config)
    app.use(router).use(createBootstrap())
    app.component('font-awesome-icon', FontAwesomeIcon)
    app.mount(container)
}

if (import.meta.env.MODE === 'development') {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  const store = useAppConfig(pinia)
  store.setConfig({ userName: 'DevUser', theme: 'light', baseUrl: '/opennms' })
  app.use(router).use(createBootstrap())
  app.component('font-awesome-icon', FontAwesomeIcon)
  app.mount('#app')
}
EOF

# 9. src/api/client.ts (Crucial Bash Escaping Applied)
cat <<EOF > "$UI_DIR/src/api/client.ts"
import axios from 'axios'
import { useAppConfig } from '../stores/appConfig'

const client = axios.create()

client.interceptors.request.use((config) => {
  const appConfig = useAppConfig()
  
  if (config.url && !config.url.startsWith('http')) {
    config.baseURL = appConfig.baseUrl
  }

  if (import.meta.env.DEV) {
    const credentials = btoa('admin:admin')
    config.headers.Authorization = \`Basic \${credentials}\`
    config.headers.Accept = 'application/json'
  }

  return config
})

export default client
EOF

# 10. src/stores/nodeStore.ts (UPDATED WITH ARRAY LOGIC)
cat <<EOF > "$UI_DIR/src/stores/nodeStore.ts"
import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '../api/client'

export const useNodeStore = defineStore('nodeStore', () => {
  const nodes = ref<any[]>([])
  const totalCount = ref(0)
  const loading = ref(false)

  async function fetchNodes() {
    loading.value = true
    try {
      // Requesting the first 25 nodes from the OpenNMS REST API
      const response = await client.get('/rest/nodes', { params: { limit: 25 } })
      
      // OpenNMS returns { node: [...], totalCount: X }
      nodes.value = response.data.node || []
      totalCount.value = response.data.totalCount || 0
    } catch (error) {
      console.error('API Error:', error)
      nodes.value = []
    } finally {
      loading.value = false
    }
  }

  return { nodes, totalCount, loading, fetchNodes }
})
EOF

# 11. index.html (Local Dev Entry Point)
cat <<EOF > "$UI_DIR/index.html"
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${PLUGIN_DESCRIPTION} - Dev</title>
    <style>
      body { margin: 0; padding: 0; background-color: #f8f9fa; }
    </style>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
EOF

# 12. Final Cleanup and Assets
touch "$UI_DIR/src/components/inventory/view/styles/requisitions.scss"
cat <<EOF > "$UI_DIR/src/App.vue"
<template>
  <router-view />
</template>
EOF

echo -e "${CLR_GREEN}Advanced UI Scaffold with Node Table Complete!${CLR_NORMAL}"