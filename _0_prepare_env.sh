#!/bin/bash
# ==============================================================================
# OpenNMS Dev Environment Setup
# Purpose: Installs Node.js 20 (LTS), NPM, and Maven for Plugin Development.
# ==============================================================================
set -e

# --- Color Definitions ---
CLR_GREEN='\033[0;32m'
CLR_RED='\033[0;31m'
CLR_NORMAL='\033[0m'

echo -e "${CLR_GREEN}🛠️  Starting Environment Setup...${CLR_NORMAL}"

# 1. Update and install basic development tools
echo "* Installing Base Development Tools (GCC, Make, etc.)..."
sudo dnf groupinstall "Development Tools" -y

# 2. Reset and Enable Node.js 20 Stream
# Vue 3 and Vite 7 require at least Node 18+. Node 20 is the current stable LTS.
echo "* Configuring Node.js 20 Repository..."
sudo dnf module reset nodejs -y
sudo dnf module enable nodejs:20 -y

# 3. Install Node.js, NPM, and Maven
echo "* Installing Node.js, NPM, and Maven..."
sudo dnf install nodejs maven -y

# 4. Verification Block
echo -e "\n${CLR_GREEN}✅ Installation Verification:${CLR_NORMAL}"

# Check Node
if command -v node >/dev/null 2>&1; then
    echo "  - Node.js: $(node -v)"
else
    echo -e "  - ${CLR_RED}Node.js: NOT FOUND${CLR_NORMAL}"
fi

# Check NPM
if command -v npm >/dev/null 2>&1; then
    echo "  - NPM:     v$(npm -v)"
else
    echo -e "  - ${CLR_RED}NPM:     NOT FOUND${CLR_NORMAL}"
fi

# Check Maven
if command -v mvn >/dev/null 2>&1; then
    echo "  - Maven:   $(mvn -version | head -n 1)"
else
    echo -e "  - ${CLR_RED}Maven:   NOT FOUND${CLR_NORMAL}"
fi

echo -e "\n${CLR_GREEN}Environment is ready for your _5_build_and_deploy.sh script!${CLR_NORMAL}"