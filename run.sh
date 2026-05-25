#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# 1. Check for virtual environment and create if missing
if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment..."
    python -m venv .venv
fi

# 2. Activate venv
source .venv/bin/activate

# 3. Install/Update dependencies
echo "[*] Ensuring dependencies are up to date..."
pip install -r requirements.txt > /dev/null

# 4. Start the utility
echo "[*] Launching OBS Utility..."
python -m obs_utility