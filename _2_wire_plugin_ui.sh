#!/bin/bash
# ==============================================================================
# OpenNMS Plugin Scaffolding Script
# Based on: https://github.com/OpenNMS/opennms-integration-api/blob/master/sample/README.md
#
# PURPOSE:
# This script automates the creation of a new OpenNMS OSGi plugin. It performs 
# three high-level tasks:
#   1. Syncs with the official OpenNMS Integration API repository.
#   2. Extracts and refactors the "SampleUIExtension.java" template.
#   3. Deploys the refactored code into the new project structure.
#
# WHY IS SampleUIExtension.java IMPORTANT?
# In the OpenNMS Integration API architecture, the UIExtension class acts as the 
# "Glue" between your backend plugin and the OpenNMS Web Console. 
# Without this file:
#   - Your plugin will remain "invisible" to the OpenNMS UI.
#   - You won't have a registered entry in the navigation menus.
#   - The system won't know where to find your frontend JavaScript bundles (.es.js).
#
# By copying and refactoring this file, we ensure the plugin is correctly 
# registered as an OSGi service that the OpenNMS ReST and Web layers can detect.
# ==============================================================================

# Exit immediately if a command exits with a non-zero status
set -e

# --- Color Definitions for Terminal Output ---
CLR_GREEN='\033[0;32m'
CLR_NORMAL='\033[0m'

# --- Project Configuration ---
REPO_VER="1.6.1"                # Target version of the Integration API
KARAF_VER="4.3.10"              # Target Karaf container version
MAVEN_BUNDLE_PLUGIN_VER="5.1.2" # Plugin for OSGi manifest generation
PLUGIN_VERSION="1.0.0"          # Initial version of your new plugin
PLUGIN_NAME="my_plugin_name"    # Internal artifact ID/directory name
PLUGIN_DESCRIPTION="my_plugin_description" # User-facing name in OpenNMS UI
UI_EXTENSION_DIR="ui-$PLUGIN_NAME"

# --- Environment Setup ---
COMPANY="mycompany"             # Organization namespace
OPENNMS_REPO="$HOME/my_github_repo/"
HERE=`pwd`

# --- Step 1: Clone Integration API ---
# We fetch the official repository to ensure we have the most accurate 
# boilerplate code for the current Integration API version.
echo "* Preparing OpenNMS Integration API environment..."
mkdir -p "$OPENNMS_REPO"
cd "$OPENNMS_REPO"

if [ ! -d "opennms-integration-api" ]; then
    git clone https://github.com/OpenNMS/opennms-integration-api/   
fi

# --- Step 2: Version Control ---
# Checkout the specific version tag to ensure the SampleUIExtension API 
# signatures match the Karaf version we are targeting.
cd "$OPENNMS_REPO/opennms-integration-api"
echo -n "* Setting correct tag (v$REPO_VER) in opennms-integrations-api repo..."
git checkout "v$REPO_VER" --quiet

# --- Step 3: Template Extraction ---
# We create a temporary workspace to refactor the SampleUIExtension.java file.
# We DO NOT edit it in the repo directly to keep the API clone clean.
TMPDIR=`mktemp -d`
cd "$TMPDIR"
echo -n "* Extracting SampleUIExtension.java from API source..."
cp "$OPENNMS_REPO/opennms-integration-api/sample/src/main/java/org/opennms/integration/api/sample/SampleUIExtension.java" .
echo -e "${CLR_GREEN}DONE${CLR_NORMAL}"

# --- Step 4: Class Refactoring (Renaming & Namespacing) ---
# 1. We rename the file to match our Plugin Name (e.g., MyPluginUIExtension.java).
# 2. We use 'sed' to update the class name inside the code.
# 3. We update the 'package' declaration so it resides in our company namespace.
camel_name="${PLUGIN_NAME^}"
class_name="${camel_name}UIExtension"
NEW_FILE="$class_name".java

echo -n "* Refactoring: Renaming to $class_name and updating package..."
mv SampleUIExtension.java "$NEW_FILE"
sed -i "s/SampleUIExtension/$class_name/g" "$NEW_FILE"
sed -i "s/org.opennms.integration.api.sample/com.$COMPANY.$PLUGIN_NAME/g" "$NEW_FILE"

# --- Step 5: Final Placement ---
# Finally, we move the custom-branded UI Extension into the plugin source tree.
# This makes the file a permanent part of your new project's Java source code.
cd "$HERE"
DEST_DIR="$PLUGIN_NAME/plugin/src/main/java/com/$COMPANY/$PLUGIN_NAME"

# Ensure the directory exists (Force create to support one-pass generation)
mkdir -p "$DEST_DIR"

echo -n "* Deploying refactored $NEW_FILE to project source..."
cp "$TMPDIR/$NEW_FILE" "$DEST_DIR/"
echo -e "${CLR_GREEN}DONE${CLR_NORMAL}"

# Clean up temp directory
rm -rf "$TMPDIR"