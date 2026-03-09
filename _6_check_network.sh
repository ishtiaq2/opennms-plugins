#!/bin/bash
# ==============================================================================
# OpenNMS Connectivity Check
# Purpose: Verifies the Host -> Container network path for the Dev Proxy.
# ==============================================================================
source ./_0_config.sh

echo "* Testing connectivity to OpenNMS Container..."

# 1. Check if the port is open on the host
if nc -z localhost 8980; then
    echo -e "${CLR_GREEN}✅ Port 8980 (Web UI/API) is open on localhost.${CLR_NORMAL}"
else
    echo -e "${CLR_RED}❌ Port 8980 is NOT reachable. Is the container running?${CLR_NORMAL}"
    exit 1
fi

# 2. Test the 'whoami' REST endpoint (Checks if API is responsive)
echo "* Testing OpenNMS REST API (WhoAmI)..."
RESPONSE=$(curl -s -u admin:admin http://localhost:8980/opennms/rest/whoami)

if [[ $RESPONSE == *"admin"* ]]; then
    echo -e "${CLR_GREEN}✅ REST API responded successfully.${CLR_NORMAL}"
else
    echo -e "${CLR_RED}❌ REST API failed to respond. Check OpenNMS logs.${CLR_NORMAL}"
    exit 1
fi

echo -e "\n${CLR_GREEN}Network is verified. You can now run: npm run dev${CLR_NORMAL}"