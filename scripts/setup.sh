#!/bin/bash
# setup.sh - Install project dependencies

# Exit immediately if a command exits with a non-zero status
set -e

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
# Ensure requirements.txt exists in the root directory or adjust path
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  echo "Error: requirements.txt not found!"
  exit 1
fi

echo "Setup complete."