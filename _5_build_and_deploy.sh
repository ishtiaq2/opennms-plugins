#!/bin/bash
# ==============================================================================
# OpenNMS Plugin: Build and Hot-Deploy
# ==============================================================================
set -e
source ./_0_config.sh

# Target server info (Adjust these or pass as arguments)
DEPLOY_IP=${1:-"192.168.1.181"}
CONTAINER_NAME="opennms-container"
DEPLOY_PATH="/opt/opennms/deploy/"

echo -e "${CLR_GREEN}🚀 Starting Build and Deploy for $PLUGIN_NAME...${CLR_NORMAL}"

# --- 1. Frontend Build ---
echo "* Step 1: Building Frontend Assets..."
cd "$PLUGIN_NAME/ui-extension"
npm install
npm run build
cd - > /dev/null

# --- 2. Java / Maven Build ---
echo "* Step 2: Compiling Java Plugin and Creating KAR..."
cd "$PLUGIN_NAME"
# -U forces update of snapshots, -DskipTests speeds up the dev cycle
mvn clean install -DskipTests -U
cd - > /dev/null

# --- 3. Deployment ---
KAR_FILE=$(ls "$PLUGIN_NAME/assembly/target/"*.kar | head -n 1)

if [ -z "$KAR_FILE" ]; then
    echo -e "${CLR_RED}Error: .kar file not found in assembly/target!${CLR_NORMAL}"
    exit 1
fi

echo "* Step 3: Deploying $KAR_FILE to $CONTAINER_NAME..."

if [ "$DEPLOY_IP" == "localhost" ]; then
    # Local Container Deploy
    podman cp "$KAR_FILE" "${CONTAINER_NAME}:${DEPLOY_PATH}"
else
    # Remote Server Deploy (Requires SSH access)
    scp "$KAR_FILE" "maven-admin@${DEPLOY_IP}:/tmp/"
    ssh "maven-admin@${DEPLOY_IP}" "podman cp /tmp/$(basename "$KAR_FILE") ${CONTAINER_NAME}:${DEPLOY_PATH}"
fi

# --- 4. Verification ---
echo -e "${CLR_GREEN}✅ Deployment Complete!${CLR_NORMAL}"
echo "* OpenNMS will now auto-deploy the KAR file."
echo "* Check logs with: podman logs -f $CONTAINER_NAME | grep $PLUGIN_NAME"