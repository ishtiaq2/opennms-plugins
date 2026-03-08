To find the specific documentation for developing a UI extension in Horizon 35, 
you should bookmark the following sections of the OpenNMS Documentation Portal.

# 1. The Primary Guide (Plugin Development)
    The "OIA" (OpenNMS Integration API) guide is your main instruction manual. It explains how to set up your project and how to specifically build a UI extension.

    Horizon 35 Plugin Development Guide: docs.opennms.com/horizon/35/development/oia/introduction.html
    
    Specific UI Extension Section: Look for the "Web UI Extensions" chapter within that same guide. It details how to use the UiExtension class to define where your plugin appears (e.g., in the navigation bar or on the node details page).

# 2. The API Reference (For your code)
    While coding, you will need to know what Java methods are available. The "Integration API" is versioned separately from Horizon itself.

    Integration API Documentation: github.com/OpenNMS/opennms-integration-api
    
    Tip: Scroll down to the "Features" section in the README. It lists the interfaces you can implement (like AlarmPersisterExtension or UiExtension).

# 3. The "Design System" (For your UI look and feel)
    Modern OpenNMS UI extensions use Vue.js and the Feather Design System. To make your plugin look like part of OpenNMS, you should reference the Feather components.

    Feather Design System: feather.opennms.io
    
    This site provides the code snippets for buttons, cards, and tables that you will use in your Vue components.
    
    Where to find the "Successful Code Patterns"
    As mentioned, the best way to learn is by looking at working examples.
    
    Go to the OpenNMS Integration API Examples on GitHub.
    
    Look for the folder named example-ui-extension.
    
    Check plugin/src/main/java/... to see how they register the extension in Java.
    
    Check plugin/src/main/resources/ui/... to see how they wrote the Vue.js frontend code.
