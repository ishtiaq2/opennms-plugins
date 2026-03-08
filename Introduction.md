OpenNMS Plugin API
https://github.com/OpenNMS/opennms-integration-api
https://www.opennms.com/opennms-plugin-api/

Plugin Development with the OpenNMS Plugin API
https://docs.opennms.com/horizon/35/development/oia/introduction.html

Think of these three links as different "views" of the same engine. 
While they all point toward the OpenNMS Integration API (OIA), they 
serve very different purposes for a developer.

Here is the breakdown of the differences:

# 1. The Source Code (GitHub)
   Link: OpenNMS/opennms-integration-api
   https://github.com/OpenNMS/opennms-integration-api

    What it is: The actual "blueprint" and code for the API.

    Best for: * Advanced Reference: Looking at the raw Java interfaces to see exactly what methods are available.

    Examples: Browsing the examples/ directory in the repo to see how real plugins are structured.

    Issue Tracking: Reporting bugs in the API itself or seeing what new features are being added in the next version.

    Education Note: You go here when the documentation doesn't explain a specific edge case and you need to see the "truth" in the code.

# 2. The Marketing & Strategy Page (OpenNMS.com)
   Link: OpenNMS Plugin API Overview
   https://www.opennms.com/opennms-plugin-api/

    What it is: A high-level overview of the "Plugin Ecosystem."

    Best for: * Understanding the "Why": Explaining to a manager or a teammate why using the OIA is better than 
   hacking the core OpenNMS code (it offers stability and version compatibility).
    
    Feature List: A quick list of what you can actually do with the API (e.g., "Can I write a Ticketer? Yes. 
   Can I write a custom Topology provider? Yes.").
    
    Version Compatibility: Checking which version of the API works with which version of Horizon/Meridian.
    
    Education Note: This is the "brochure." It helps you understand the scope of what is possible before you start coding.

# 3. The "How-To" Manual (Horizon Documentation)
   Link: Plugin Development with OIA
   https://docs.opennms.com/horizon/35/development/oia/introduction.html

    What it is: The step-by-step instructional guide specifically for the version of OpenNMS you are running (Horizon 35).
    
    Best for: * Getting Started: This contains the "Quick Start" guide and the Maven commands to generate your project.
    
    UI Extensions: Specific instructions on how to hook into the Web UI (your specific goal).
    
    Environment Setup: Details on how to set up your IDE, build the project, and deploy the resulting .kar file.
    
    Education Note: This is your primary textbook. Follow this link first for your UI-extension project.
