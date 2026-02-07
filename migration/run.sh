#!/bin/bash
# Run the news scanner demo
#
# This script uses a local Node.js installation to avoid WSL/Windows path issues.
# If you have Linux node installed, you can run: node demo.mjs directly.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_DIR="$HOME/node-v20.11.0-linux-x64/bin"

# Check if local node exists
if [ -x "$NODE_DIR/node" ]; then
    export PATH="$NODE_DIR:$PATH"
    echo "Using Node.js from: $NODE_DIR"
else
    echo "Local Node.js not found. Checking system node..."
    # Filter out Windows paths
    export PATH=$(echo $PATH | tr ':' '\n' | grep -v '/mnt/c' | tr '\n' ':')

    if ! command -v node &> /dev/null; then
        echo ""
        echo "ERROR: No Linux Node.js found."
        echo ""
        echo "To install Node.js in WSL, run:"
        echo "  cd ~"
        echo "  curl -sL https://nodejs.org/dist/v20.11.0/node-v20.11.0-linux-x64.tar.xz -o node.tar.xz"
        echo "  tar -xf node.tar.xz"
        echo ""
        echo "Then run this script again."
        exit 1
    fi
fi

echo "Node version: $(node --version)"
echo ""

cd "$SCRIPT_DIR"
node demo.mjs "$@"
