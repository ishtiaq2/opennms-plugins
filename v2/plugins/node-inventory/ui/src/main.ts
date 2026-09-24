import NodeInventory from './NodeInventory.vue'

// How the OpenNMS UI mounts this plugin (ui/src/components/Plugin/utils.ts in OpenNMS 33.1.8):
//   1. it adds <script type="module" crossorigin="use-credentials" src="
//        /opennms/rest/plugins/ui-extension/module/<extensionId>?path=<resourceRoot>/<moduleFile>">
//   2. when the script has run, it reads window[<extensionId>] and renders that component.
// So the only thing this entry point must do is publish the component under the extension id.
;(window as unknown as Record<string, unknown>)[__EXTENSION_ID__] = NodeInventory
