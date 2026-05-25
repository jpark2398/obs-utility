import subprocess
import json

def get_active_audio_streams():
    """Queries PipeWire directly to find the names of active audio streams exactly as OBS sees them."""
    try:
        # Ask PipeWire for its current state
        result = subprocess.run(['pw-dump'], capture_output=True, text=True)
        pw_data = json.loads(result.stdout)
        
        active_streams = set()
        
        for item in pw_data:
            # We only care about Nodes (endpoints) in the audio graph
            if item.get('type') == 'PipeWire:Interface:Node':
                props = item.get('info', {}).get('props', {})
                
                # Check if this node is an application sending audio out
                media_class = props.get('media.class')
                if media_class == 'Stream/Output/Audio':
                    
                    # PipeWire stores the human-readable name in a few possible keys depending on the app/Proton
                    app_name = (
                        props.get('application.name') or 
                        props.get('media.name') or 
                        props.get('node.name')
                    )
                    
                    if app_name:
                        # Clean up common Wine/Proton prefixes if they exist
                        clean_name = app_name.replace('ALSA plug-in [', '').replace(']', '')
                        active_streams.add(clean_name)
                        
        return active_streams

    except Exception as e:
        print(f"[!] PipeWire query failed: {e}")
        return set()


if __name__ == "__main__":
    streams = get_active_audio_streams()
    print(f"Currently active audio streams OBS can see: {streams}")
