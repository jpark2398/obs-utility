import obspython as obs
import subprocess
import json
import uuid
import os
import time

# --- Configuration & Absolute Paths ---
source_name = ""  # Now set dynamically by the OBS UI
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "audio_config.json")
POPUP_PATH = os.path.join(SCRIPT_DIR, "popup_manager.py")
TEMP_CHOICE = os.path.join(SCRIPT_DIR, "temp_choice.json")

VENV_PYTHON = os.path.join(SCRIPT_DIR, ".venv", "bin", "python")

# --- Globals for Locking & Session State ---
pending_streams = set()
session_ignored = set()

# --- Persistence ---
def load_persistence():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f: return json.load(f)
        except: pass
    return {"whitelist": [], "ignored": []}

def save_persistence(data):
    try:
        with open(CONFIG_PATH, "w") as f: json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[OBS Utility] Failed to save persistence: {e}")

persistence = load_persistence()

# --- Utility Helpers ---
def release_obs_pointers(source, settings, apps_array):
    """Safely releases memory for OBS C-pointers."""
    obs.obs_data_array_release(apps_array)
    obs.obs_data_release(settings)
    obs.obs_source_release(source)

# --- Core Logic Functions ---

def process_pending_choice(apps_array):
    """
    Step 5: Execute user's choice.
    Returns (handled_choice: bool, added_to_obs: bool)
    """
    global pending_streams, session_ignored
    if not os.path.exists(TEMP_CHOICE):
        return False, False
        
    added_to_obs = False
    try:
        with open(TEMP_CHOICE, "r") as f: choice = json.load(f)
        stream_name = choice.get("stream")
        
        if choice.get("add"):
            # User clicked 'Yes'
            persistence["whitelist"].append(stream_name)
            new_item = obs.obs_data_create()
            obs.obs_data_set_string(new_item, "uuid", str(uuid.uuid4()))
            obs.obs_data_set_string(new_item, "value", stream_name)
            obs.obs_data_set_bool(new_item, "hidden", False)
            obs.obs_data_set_bool(new_item, "selected", True)
            obs.obs_data_array_push_back(apps_array, new_item)
            obs.obs_data_release(new_item)
            added_to_obs = True
            save_persistence(persistence)
            print(f"[OBS Utility] Added {stream_name} from popup.")
            
        elif choice.get("dont_ask"):
            # User clicked 'Don't ask again'
            persistence["ignored"].append(stream_name)
            save_persistence(persistence)
            print(f"[OBS Utility] Permanently ignored {stream_name}.")
            
        else:
            # User clicked 'No' (or closed the window)
            session_ignored.add(stream_name)
            print(f"[OBS Utility] Ignored {stream_name} for this session.")
        
    except Exception as e:
        print(f"[OBS Utility] Choice Error: {e}")
    finally:
        if os.path.exists(TEMP_CHOICE): 
            try: os.remove(TEMP_CHOICE)
            except: pass
        pending_streams.clear()
        
    return True, added_to_obs

def is_popup_locked():
    """Checks memory lock."""
    global pending_streams
    if not pending_streams:
        return False
        
    return True

def enforce_whitelist(apps_array):
    """
    Step 1a: Ensure everything in the JSON whitelist is in the OBS source.
    Returns True if the array was modified.
    """
    existing_in_obs = set()
    for i in range(obs.obs_data_array_count(apps_array)):
        item = obs.obs_data_array_item(apps_array, i)
        val = obs.obs_data_get_string(item, "value")
        if val: existing_in_obs.add(val)
        obs.obs_data_release(item)

    needs_update = False
    for whitelist_app in persistence["whitelist"]:
        if whitelist_app not in existing_in_obs:
            new_item = obs.obs_data_create()
            obs.obs_data_set_string(new_item, "uuid", str(uuid.uuid4()))
            obs.obs_data_set_string(new_item, "value", whitelist_app)
            obs.obs_data_set_bool(new_item, "hidden", False)
            obs.obs_data_set_bool(new_item, "selected", True)
            obs.obs_data_array_push_back(apps_array, new_item)
            obs.obs_data_release(new_item)
            
            existing_in_obs.add(whitelist_app)
            needs_update = True
            print(f"[OBS Utility] Whitelist Enforced: Added '{whitelist_app}'")
            
    return needs_update

def get_pipewire_streams():
    """Step 2: Detect programs USING native PipeWire data."""
    try:
        result = subprocess.run(['pw-dump'], capture_output=True, text=True, timeout=2.0)
        pw_data = json.loads(result.stdout)
        active_streams = set()
        for item in pw_data:
            if item.get('type') == 'PipeWire:Interface:Node':
                props = item.get('info', {}).get('props', {})
                if props.get('media.class') == 'Stream/Output/Audio':
                    name = props.get('application.name') or props.get('media.name')
                    if name:
                        active_streams.add(name.replace('ALSA plug-in [', '').replace(']', ''))
        return active_streams
    except Exception as e:
        print(f"[OBS Utility] PipeWire API timeout/error: {e}")
        return set()

def prompt_new_streams(detected_streams):
    """Step 3 & 4: Launch popup for untracked streams."""
    global pending_streams, session_ignored
    for stream in detected_streams:
        # Now checks against the session_ignored set as well
        if stream in persistence["whitelist"] or stream in persistence["ignored"] or stream in session_ignored:
            continue
            
        print(f"[OBS Utility] PipeWire detected new stream: {stream}. Spawning popup.")
        
        pending_streams.add(stream)
        
        try:
            env = os.environ.copy()
            env["DISPLAY"] = os.environ.get("DISPLAY", ":0")
            subprocess.Popen([VENV_PYTHON, POPUP_PATH, stream], env=env)
        except Exception as e:
            print(f"[OBS Utility] Error spawning popup: {e}")
            pending_streams.clear()
            
        break # Lock guarantees only one popup spawns per tick

# --- Main Orchestrator ---

def update_obs_source():
    """Main timer loop orchestrating the flow."""
    if not source_name: 
        return # Do nothing if the user hasn't selected a source in the UI yet
        
    source = obs.obs_get_source_by_name(source_name)
    if not source: return

    settings = obs.obs_source_get_settings(source)
    apps_array = obs.obs_data_get_array(settings, "apps")
    
    # 5. Execute user's choice (Resolves the lock)
    handled_choice, added_to_obs = process_pending_choice(apps_array)
    if handled_choice:
        if added_to_obs:
            obs.obs_data_set_array(settings, "apps", apps_array)
            obs.obs_source_update(source, settings)
        release_obs_pointers(source, settings, apps_array)
        return

    # Check memory lock
    if is_popup_locked():
        release_obs_pointers(source, settings, apps_array)
        return

    # 1a. Enforce JSON whitelist into the OBS audio source
    if enforce_whitelist(apps_array):
        obs.obs_data_set_array(settings, "apps", apps_array)
        obs.obs_source_update(source, settings)

    # 2. Detect programs USING native PipeWire data
    detected_streams = get_pipewire_streams()

    # 3 & 4. Check if they are in the source, if not launch popup
    prompt_new_streams(detected_streams)

    # Cleanup memory
    release_obs_pointers(source, settings, apps_array)

# --- UI & Lifecycle ---

def open_config_btn_clicked(props, prop):
    """Callback for the 'Open audio_config.json' button."""
    try:
        # xdg-open is the universal Linux command to open a file in the default text editor
        subprocess.Popen(['xdg-open', CONFIG_PATH])
    except Exception as e:
        print(f"[OBS Utility] Error opening config: {e}")
    return False # Return False so the UI doesn't artificially refresh

def script_properties():
    """Defines the OBS UI properties for the script window."""
    props = obs.obs_properties_create()
    
    # 1. Dropdown for the Audio Source
    p = obs.obs_properties_add_list(
        props, 
        "source_name", 
        "PipeWire Source", 
        obs.OBS_COMBO_TYPE_LIST, 
        obs.OBS_COMBO_FORMAT_STRING
    )
    
    # Populate the dropdown with ONLY PipeWire Application Capture sources
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            # The Linux plugin ID contains 'pipewire', this safely excludes 
            # standard mics, webcams, and browser sources.
            if "pipewire" in source_id.lower() or "application_audio_capture" in source_id.lower():
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)
        obs.source_list_release(sources)

    # 2. Button to open the JSON config
    obs.obs_properties_add_button(
        props, 
        "open_config", 
        "📝 Open audio_config.json", 
        open_config_btn_clicked
    )
    
    return props

def script_defaults(settings):
    """Sets default UI values when the script is first loaded."""
    obs.obs_data_set_default_string(settings, "source_name", "Game Audio")

def script_update(settings):
    """Fires whenever the user changes a setting in the UI."""
    global source_name
    source_name = obs.obs_data_get_string(settings, "source_name")

def script_load(settings): 
    obs.timer_add(update_obs_source, 5000)

def script_unload(): 
    global pending_streams, session_ignored
    obs.timer_remove(update_obs_source)
    pending_streams.clear()
    session_ignored.clear()
    if os.path.exists(TEMP_CHOICE):
        try: os.remove(TEMP_CHOICE)
        except: pass