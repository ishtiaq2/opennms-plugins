#!/bin/bash
# ==============================================================================
# OpenNMS Plugin Scaffolding Script
# Purpose: Generates a plugin skeleton and cleans out archetype boilerplate
# ==============================================================================

REPO_VER="1.6.1"
KARAF_VER="4.3.10"
MAVEN_BUNDLE_PLUGIN_VER="5.1.2"
PLUGIN_VERSION="1.0.0"
PLUGIN_NAME="my_plugin_name"
PLUGIN_DESCRIPTION="my_plugin_description"
UI_EXTENSION_DIR="ui-$PLUGIN_NAME"
COMPANY="mycompany"
OPENNMS_REPO="$HOME/my_github_repo/opennms-lab/"
HERE=`pwd`

# --- Step 1: Initial Cleanup ---
# Ensure we aren't working on top of an old build
if [ -d "$PLUGIN_NAME" ]; then
  echo "* Removing existing plugin directory: $PLUGIN_NAME"
  rm -rf -- "$PLUGIN_NAME"
fi  

# --- Step 2: Skeleton Generation ---
echo "* Generating Maven archetype..."

mvn archetype:generate -B \
  -DarchetypeGroupId=org.opennms.integration.api \
  -DarchetypeArtifactId=example-kar-plugin \
  -DarchetypeVersion=1.0.0 \
  -DgroupId=com.$COMPANY \
  -DartifactId=$PLUGIN_NAME \
  -Dversion=$PLUGIN_VERSION \
  -Dpackage=com.$COMPANY.$PLUGIN_NAME \
  -DpluginId=$PLUGIN_NAME \
  -DpluginName="$PLUGIN_DESCRIPTION"

# --- Step 3: Boilerplate Removal ---
# The archetype creates several "Example" files we usually don't want.
echo "* Cleaning boilerplate from generated source folders..."

# 1. Clear Java source files (removes ExampleListener.java, etc.)
JAVA_SRC_DIR="$PLUGIN_NAME/plugin/src/main/java/com/$COMPANY/$PLUGIN_NAME"
if [ -d "$JAVA_SRC_DIR" ]; then
    rm -rf "${JAVA_SRC_DIR:?}"/*
    echo "  - Cleared: $JAVA_SRC_DIR"
fi

# 2. Clear events configuration (removes example event XMLs)
EVENTS_DIR="$PLUGIN_NAME/plugin/src/main/resources/events"
if [ -d "$EVENTS_DIR" ]; then
    rm -rf "${EVENTS_DIR:?}"/*
    echo "  - Cleared: $EVENTS_DIR"
fi

# 3. Clear all test files
TEST_DIR="$PLUGIN_NAME/plugin/src/test"
if [ -d "$TEST_DIR" ]; then
    rm -rf "${TEST_DIR:?}"/*
    echo "  - Cleared: $TEST_DIR"
fi

echo "* Scaffolding complete. Ready for custom code injection."