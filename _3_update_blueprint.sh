#!/bin/bash
# ==============================================================================
# OSGi Blueprint Configuration Generator
# ==============================================================================
# PURPOSE:
# This step creates a "Bare Minimum" blueprint.xml. In OSGi environments (like 
# Karaf/OpenNMS), the Blueprint container is responsible for dependency 
# injection and service exportation.
#
# WHY OVERWRITE?
# Standard Maven archetypes often include "Reference" dependencies (like Alarms 
# or Nodes). If those services aren't available when the plugin starts, the 
# plugin will hang in a "GracePeriod" state. By using a "Bare Minimum" config,
# we ensure the plugin starts immediately and only registers the UI.
#
# KEY COMPONENTS:
#   - <service>: Exports the Java class so OpenNMS can "see" the plugin.
#   - interface: Must match the official OpenNMS Integration API UIExtension.
#   - bean class: The fully qualified name of your refactored Java class.
# ==============================================================================

# --- Configuration (Must match _1_ and _2_) ---
PLUGIN_NAME="my_plugin_name"
COMPANY="mycompany"
PLUGIN_DESCRIPTION="my_plugin_description"
# Recover the class name logic from script _2_
camel_name="${PLUGIN_NAME^}"
class_name="${camel_name}UIExtension"

# Target path 
BP_FILE="$PLUGIN_NAME/plugin/src/main/resources/OSGI-INF/blueprint/blueprint.xml"
# ... rest of your script ...
# --- Blueprint Generation (Heredoc) ---
# We use a Heredoc (cat <<EOF) to maintain XML readability while injecting 
# our dynamic script variables.
cat <<EOF > "$BP_FILE"
<blueprint xmlns="http://www.osgi.org/xmlns/blueprint/v1.0.0" 
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.osgi.org/xmlns/blueprint/v1.0.0 
                http://www.osgi.org/xmlns/blueprint/v1.0.0/blueprint.xsd">

    <service id="uiExtension" interface="org.opennms.integration.api.v1.ui.UIExtension">
        <bean class="com.$COMPANY.$PLUGIN_NAME.$class_name">
            <property name="id" value="uiExtension"/>
            <property name="menuEntry" value="$PLUGIN_DESCRIPTION"/>
            <property name="resourceRoot" value="ui-ext"/>
            <property name="moduleFileName" value="uiextension.es.js"/>
        </bean>
    </service>

</blueprint>
EOF

# --- Final Status Check ---
if [ $? -eq 0 ]; then
    echo -e "${CLR_GREEN}DONE${CLR_NORMAL}"
    echo "  - Service: com.$COMPANY.$PLUGIN_NAME.$class_name"
    echo "  - Menu Entry: $PLUGIN_DESCRIPTION"
else
    echo -e "${CLR_RED}FAILED to write Blueprint configuration${CLR_NORMAL}"
    exit 1
fi