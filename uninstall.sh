#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the absolute path to the repo directory
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.gh-menu.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$PLIST_NAME"

echo "================================================"
echo "gh-menu Uninstall Script"
echo "================================================"
echo ""

# Check if Launch Agent is loaded
if launchctl list | grep -q "com.gh-menu"; then
    echo "Unloading Launch Agent..."
    if launchctl unload "$PLIST_PATH" 2>/dev/null; then
        echo -e "${GREEN}✓ Launch Agent unloaded${NC}"
    else
        echo -e "${YELLOW}⚠ Could not unload Launch Agent (it may not be running)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Launch Agent is not currently loaded${NC}"
fi

# Remove plist from LaunchAgents
if [ -f "$PLIST_PATH" ]; then
    echo ""
    echo "Removing Launch Agent plist..."
    rm "$PLIST_PATH"
    echo -e "${GREEN}✓ Removed $PLIST_PATH${NC}"
else
    echo -e "${YELLOW}⚠ Launch Agent plist not found at $PLIST_PATH${NC}"
fi

# Remove local plist copy
if [ -f "$REPO_DIR/$PLIST_NAME" ]; then
    echo ""
    echo "Removing local plist copy..."
    rm "$REPO_DIR/$PLIST_NAME"
    echo -e "${GREEN}✓ Removed $REPO_DIR/$PLIST_NAME${NC}"
fi

# Ask about removing .env file
if [ -f "$REPO_DIR/.env" ]; then
    echo ""
    read -p "Remove .env file (contains your GitHub API key)? [Y/n] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${YELLOW}⚠ Kept .env file${NC}"
    else
        rm "$REPO_DIR/.env"
        echo -e "${GREEN}✓ Removed .env file${NC}"
    fi
fi

# Success message
echo ""
echo "================================================"
echo -e "${GREEN}Uninstall Complete!${NC}"
echo "================================================"
echo ""
echo "The gh-menu app has been removed from startup."
echo ""
echo "The following were NOT removed:"
echo "  - Virtual environment (.venv/)"
echo "  - Log files (~/Library/Logs/gh-menu/)"
echo "  - Dependencies installed via uv"
echo ""
echo "To completely remove the project:"
echo "  cd .. && rm -rf $(basename "$REPO_DIR")"
echo ""
