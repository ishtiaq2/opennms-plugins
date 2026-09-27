/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

/** Replaced at build time by vite.config.ts (define). */
declare const __EXTENSION_ID__: string
