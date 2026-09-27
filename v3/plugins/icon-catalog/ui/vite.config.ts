import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteExternalsPlugin } from 'vite-plugin-externals'

// The plugin's contract with OpenNMS. Keep in sync with
// ../plugin/src/main/resources/OSGI-INF/blueprint/blueprint.xml (scripts/check_plugins.py verifies it).
const EXTENSION_ID = 'labIconCatalog' // src/main.ts assigns window[EXTENSION_ID]
const RESOURCE_ROOT = 'icon-catalog' // folder inside the bundle JAR, one path segment
const MODULE_FILE = 'iconCatalog.es.js' // must contain ".es"

export default defineConfig({
  plugins: [
    vue(),
    // The OpenNMS UI (33.1.8 ships Vue 3.3.7, Pinia 2.1.7, vue-router 4.2.5) exposes its own
    // copies as window.Vue / window.Pinia / window.VueRouter. Use them instead of bundling a
    // second Vue: one runtime, shared reactivity, smaller module.
    viteExternalsPlugin({ vue: 'Vue', pinia: 'Pinia', 'vue-router': 'VueRouter' })
  ],
  define: {
    // Library mode leaves process.env.* alone, and browsers have no "process" object.
    'process.env.NODE_ENV': JSON.stringify('production'),
    __EXTENSION_ID__: JSON.stringify(EXTENSION_ID)
  },
  build: {
    // Write straight into the bundle's resources so "mvn package" picks the module up.
    outDir: fileURLToPath(new URL(`../plugin/src/main/resources/${RESOURCE_ROOT}`, import.meta.url)),
    emptyOutDir: true,
    // One CSS file: the UI requests {resourceRoot}/style.css (Vite 5 names it style.css in lib mode).
    cssCodeSplit: false,
    target: 'es2020',
    lib: {
      entry: fileURLToPath(new URL('./src/main.ts', import.meta.url)),
      formats: ['es'],
      fileName: () => MODULE_FILE
    },
    rollupOptions: {
      external: ['vue', 'pinia', 'vue-router']
    }
  }
})
