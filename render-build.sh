#!/usr/bin/env bash
# Render build script

set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies from requirements.txt
pip install -r requirements.txt

echo "Build completed successfully!"
