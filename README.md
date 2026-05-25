# OBS PipeWire Audio Router

An automated, native-feeling OBS Studio utility for Linux (Wayland/PipeWire) that dynamically detects new audio streams and prompts you to add them to your OBS audio capture sources. 

Instead of manually managing Application Audio Capture (PipeWire) properties, this script runs in the background of OBS. When a game or application launches, a clean, dark-themed popup asks if you want to route the audio directly into your stream.

## ✨ Features
* OBS Native Integration: Runs as an internal OBS script using obspython. No external daemon required.
* Native UI Configuration: Select your audio sources and manage configurations directly inside the OBS Scripts window.
* Smart PipeWire Detection: Uses pw-dump to see exactly what the OBS PipeWire capture plugin sees.
* Wayland-Compatible UI: Uses sv-ttk (Sun Valley dark theme) for a native, beautiful popup that renders flawlessly on Wayland compositors (KDE/Mutter).
* Persistent Configuration: Remembers your choices. Add to a whitelist ("Yes"), ignore for the session ("No"), or ignore permanently ("Don't ask again").
* Asynchronous & Safe: Popups run in an isolated subprocess to ensure the OBS event loop and timer never stutter or hang.

---

## 📁 Project Structure
* audio_router.py - The core OBS script.
* popup_manager.py - The isolated GUI subprocess that handles user prompts.
* install.sh - Automated deployment script.
* audio_config.json - Your persistent whitelist and ignore list.
* icon.png - The OS-level window icon for the Wayland popup.

---

## 🛠️ Prerequisites
* OS: Linux (Tested on Wayland / Arch-based systems)
* Audio: PipeWire 
* OBS Studio: With Python scripting enabled
* System Packages: Python 3, Tkinter

If you are on an Arch-based system, you can ensure you have the required dependencies with:
sudo pacman -S pipewire python tk

---

## 🚀 Installation 

This project includes an automated installation script that safely deploys the tool to your OBS configuration directory and builds an isolated Python virtual environment for the UI themes.

1. Clone or download this repository.
2. Make the installer executable and run it:

chmod +x install.sh
./install.sh

What the script does:
* Creates an installation directory at ~/.config/obs-studio/scripts/obs-audio-router/
* Builds an isolated .venv and installs the required sv-ttk UI dependencies.
* Copies the Python scripts and safely preserves your audio_config.json if you are updating.

---

## ⚙️ OBS Studio Configuration

Once the installation script completes, you need to load the tool into OBS:

1. Open OBS Studio.
2. Go to Tools > Scripts.
3. Click the Python Settings tab and ensure your system's Python install path is selected.
4. Click the Scripts tab, hit the + button, and select the newly installed script:
   ~/.config/obs-studio/scripts/obs-audio-router/audio_router.py
5. In the script properties window on the right, use the PipeWire Source dropdown to select your desired Application Audio Capture source (e.g., "Game Audio").

*Note: You can easily view or edit your saved whitelist/ignore list by clicking the "📝 Open audio_config.json" button in this menu.*

---

## 🎮 How It Works

1. Detection: Every 5 seconds, OBS checks PipeWire for new active audio streams.
2. Prompt: If an untracked stream is found, a dark-themed popup appears centered on your screen.
3. Action:
   * Yes: The application is added to your selected OBS source and saved to your permanent whitelist.
   * No: The application is ignored until you close and reopen OBS (Session Ignore).
   * Don't ask again: The application is permanently ignored and added to audio_config.json.

---

## 🐛 Troubleshooting Wayland
If the popup fails to appear, ensure that your Wayland environment variables are functioning correctly. The script attempts to pass DISPLAY and WAYLAND_DISPLAY automatically to the UI subprocess. If issues persist, check the Tools > Scripts log window in OBS for Python errors.