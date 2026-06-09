#!/bin/bash
set -e

echo "=========================================="
echo "Downloading MFScraper Agent from GitHub..."
echo "=========================================="

INSTALL_DIR="$HOME/.mfscraper-app"

if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation at $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "Cloning repository to $INSTALL_DIR..."
    git clone https://github.com/pdpraful/mfscraper.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Run the standard local install script
bash ./install.sh
