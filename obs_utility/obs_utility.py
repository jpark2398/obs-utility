import obsws_python as obs
import subprocess
import time
import json
import os
import tkinter as tk
import uuid
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================
OBS_HOST = 'localhost'
OBS_PORT = 4455
OBS_PASSWORD = os.getenv('OBS_PASSWORD')
SOURCE_NAME = "Game Audio" 

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "obs_audio_config.json")

# ==========================================
# STATE MANAGEMENT
# ==========================================
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            
            # Migration: convert old dictionaries to a list
            raw_whitelist = config.get("whitelist", [])
            if isinstance(raw_whitelist, dict):
                raw_whitelist = list(raw_whitelist.values())
                
            # Cleanup: Purge any old .exe entries lingering in the JSON
            clean_whitelist = [app for app in raw_whitelist if not app.lower().endswith('.exe')]
            config["whitelist"] = clean_whitelist
            
            return config
    return {"whitelist": [], "ignorelist": []}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# ==========================================
# PIPEWIRE POLLING
# ==========================================
def get_active_audio_streams():
    """Queries PipeWire directly to find active audio streams exactly as OBS sees them."""
    try:
        result = subprocess.run(['pw-dump'], capture_output=True, text=True)
        pw_data = json.loads(result.stdout)
        
        active_streams = set()
        desktop_noise = ["firefox", "chrome", "brave", "spotify", "discord", "obs", "telegram", "vlc", "plasma"]
        
        for item in pw_data:
            if item.get('type') == 'PipeWire:Interface:Node':
                props = item.get('info', {}).get('props', {})
                
                if props.get('media.class') == 'Stream/Output/Audio':
                    app_name = (
                        props.get('application.name') or 
                        props.get('media.name') or 
                        props.get('node.name')
                    )
                    
                    if app_name:
                        clean_name = app_name.replace('ALSA plug-in [', '').replace(']', '')
                        if any(noise in clean_name.lower() for noise in desktop_noise):
                            continue
                        active_streams.add(clean_name)
                        
        return active_streams
    except Exception as e:
        print(f"[!] PipeWire query failed: {e}")
        return set()

# ==========================================
# OBS WEBSOCKET LOGIC
# ==========================================
def update_obs_source(whitelist, cl):
    """Directly manipulates the apps array and ensures they are checked."""
    try:
        response = cl.get_input_settings(SOURCE_NAME)
        current_settings = response.input_settings
        
        existing_apps = current_settings.get('apps', [])
        existing_app_names = [app.get('value') for app in existing_apps]
        
        updated = False
        
        # 1. Add missing streams from the whitelist
        for target_name in whitelist:
            if target_name not in existing_app_names:
                new_app_entry = {
                    'hidden': False,
                    'selected': True,  # THE FIX: Ensure OBS actually captures the audio
                    'uuid': str(uuid.uuid4()),
                    'value': target_name
                }
                existing_apps.append(new_app_entry)
                updated = True
                
        # 2. Safety check: Force any existing matching entries to be selected
        for app in existing_apps:
            if app.get('value') in whitelist and not app.get('selected'):
                app['selected'] = True
                updated = True
                
        if updated:
            current_settings['apps'] = existing_apps
            cl.set_input_settings(SOURCE_NAME, current_settings, True)
            print(f"[*] OBS updated. Targets pushed and selected.")
            
    except Exception as e:
        print(f"[!] Failed to update OBS: {e}")

# ==========================================
# GUI POPUP LOGIC
# ==========================================
def ask_user(stream_name):
    """Displays a simple popup to classify a newly detected audio stream."""
    root = tk.Tk()
    root.title("OBS Utility")
    root.attributes('-topmost', True)
    
    result = {"add": False, "ignore": False}
    
    def on_yes():
        result["add"] = True
        if ignore_var.get(): result["ignore"] = False
        root.destroy()
        
    def on_no():
        result["add"] = False
        if ignore_var.get(): result["ignore"] = True
        root.destroy()

    tk.Label(root, text=f"New Audio Stream Detected:\n'{stream_name}'\n\nRoute to OBS?").pack(pady=15, padx=20)
    
    ignore_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Don't ask again (Add to ignore list)", variable=ignore_var).pack(pady=5)
    
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=15)
    tk.Button(btn_frame, text="Yes", command=on_yes, width=10, bg="green", fg="white").pack(side="left", padx=10)
    tk.Button(btn_frame, text="No", command=on_no, width=10, bg="red", fg="white").pack(side="right", padx=10)
    
    root.eval('tk::PlaceWindow . center')
    root.mainloop()
    return result

# ==========================================
# MAIN POLLING LOOP
# ==========================================
def get_obs_client():
    """Attempt to connect. Returns the client or None."""
    try:
        # We define a timeout to prevent the connection attempt from hanging
        return obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD, timeout=3)
    except Exception:
        return None

def main_loop():
    print("[*] Starting OBS Utility (PipeWire Native Mode)...")
    config = load_config()
    
    # Initialize connection state
    cl = None
    
    while True:
        # Connection Management
        if cl is None:
            cl = get_obs_client()
            if cl is None:
                print("[!] OBS not detected. Retrying in 10s...")
                time.sleep(10)
                continue
            else:
                print("[*] Successfully connected to OBS.")
                # Sync whitelist upon successful connection
                if config["whitelist"]:
                    update_obs_source(config["whitelist"], cl)

        # Main Execution Logic
        try:
            current_streams = get_active_audio_streams()
            
            for stream_name in current_streams:
                if stream_name in config["whitelist"] or stream_name in config["ignorelist"]:
                    continue
                
                print(f"[*] Unknown audio stream detected: '{stream_name}'. Prompting user...")
                user_choice = ask_user(stream_name)
                
                if user_choice["add"]:
                    config["whitelist"].append(stream_name)
                    save_config(config)
                    print(f"[+] Added '{stream_name}' to whitelist.")
                    update_obs_source(config["whitelist"], cl)
                    
                elif user_choice["ignore"]:
                    config["ignorelist"].append(stream_name)
                    save_config(config)
                    print(f"[-] Ignored '{stream_name}'.")

            time.sleep(5)
        
        # Error Handling
        except Exception as e:
            print(f"[!] Error detected: {e}. Resetting connection...")
            cl = None # Setting this to None forces the top of the loop to re-connect
            time.sleep(2)

if __name__ == "__main__":
    main_loop()
