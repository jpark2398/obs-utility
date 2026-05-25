#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_NAME="OBS Audio Router"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$PROJECT_DIR/src"
OBS_SCRIPTS_DIR="${HOME}/.config/obs-studio/scripts"
INSTALL_DIR="$OBS_SCRIPTS_DIR/obs-audio-router"
VENV_DIR="$INSTALL_DIR/.venv"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}$SCRIPT_NAME Installation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}[1/5]${NC} Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

if ! command -v pw-dump &> /dev/null; then
    echo -e "${RED}Error: PipeWire (pw-dump) is not installed${NC}"
    echo "Please install PipeWire: sudo pacman -S pipewire (or your package manager)"
    exit 1
fi

python3_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python $python3_version found"

# Create OBS scripts directory if it doesn't exist
if [ ! -d "$OBS_SCRIPTS_DIR" ]; then
    echo -e "${YELLOW}[2/5]${NC} Creating OBS scripts directory..."
    mkdir -p "$OBS_SCRIPTS_DIR"
    echo -e "${GREEN}✓${NC} Created $OBS_SCRIPTS_DIR"
else
    echo -e "${YELLOW}[2/5]${NC} OBS scripts directory exists"
    echo -e "${GREEN}✓${NC} $OBS_SCRIPTS_DIR"
fi

# Create installation directory
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}[3/5]${NC} Creating installation directory..."
    mkdir -p "$INSTALL_DIR"
    echo -e "${GREEN}✓${NC} Created $INSTALL_DIR"
else
    echo -e "${YELLOW}[3/5]${NC} Installation directory exists"
    echo -e "${GREEN}✓${NC} Updating files in $INSTALL_DIR"
fi

# Create virtual environment and install dependencies
echo -e "${YELLOW}[4/5]${NC} Setting up Python environment..."
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q -r "$PROJECT_DIR/requirements.txt"
echo -e "${GREEN}✓${NC} Python environment ready at $INSTALL_DIR"

# Copy files to OBS scripts directory
echo -e "${YELLOW}[5/5]${NC} Installing script files..."
cp "$SRC_DIR/audio_router.py" "$INSTALL_DIR/"
cp "$SRC_DIR/popup_manager.py" "$INSTALL_DIR/"
cp "$SRC_DIR/icon.png" "$INSTALL_DIR/"

# Copy or preserve config file
if [ ! -f "$INSTALL_DIR/audio_config.json" ]; then
    cp "$SRC_DIR/audio_config.json" "$INSTALL_DIR/"
    echo -e "${GREEN}✓${NC} Created new configuration file"
else
    echo -e "${GREEN}✓${NC} Preserved existing configuration file"
fi

# Set appropriate permissions
chmod 755 "$INSTALL_DIR"
chmod 644 "$INSTALL_DIR/audio_router.py"
chmod 644 "$INSTALL_DIR/popup_manager.py"
chmod 644 "$INSTALL_DIR/icon.png"
chmod 644 "$INSTALL_DIR/audio_config.json"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Open OBS Studio"
echo "2. Go to: Tools → Scripts"
echo "3. Click the + button and select:"
echo "   $INSTALL_DIR/audio_router.py"
echo "4. Add an 'Application Audio Capture' source named 'Game Audio'"
echo "5. Configure it with PipeWire as the audio backend"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "Whitelist/Ignore settings: $INSTALL_DIR/audio_config.json"
echo "Python environment: $VENV_DIR"
echo ""
