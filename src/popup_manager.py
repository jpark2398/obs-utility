import tkinter as tk
from tkinter import ttk
import sv_ttk
import json
import sys
import os

def run_popup(stream_name):
    root = tk.Tk()
    root.title("Audio Sync")
    root.attributes('-topmost', True)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_choice_path = os.path.join(script_dir, "temp_choice.json")

    icon_path = os.path.join(script_dir, "icon.png") # Put your icon here
    if os.path.exists(icon_path):
        try:
            icon_image = tk.PhotoImage(file=icon_path)
            # The 'True' flag tells it to apply to all future dialogs/windows too
            root.iconphoto(True, icon_image)
        except Exception as e:
            print(f"Could not load icon: {e}")

    def save_and_exit(add_choice, dont_ask_choice):
        try:
            with open(temp_choice_path, "w") as f:
                json.dump({"add": add_choice, "dont_ask": dont_ask_choice, "stream": stream_name}, f)
        except Exception as e:
            print(f"Error writing choice: {e}")
        finally:
            root.destroy()

    def on_closing():
        save_and_exit(False, False)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Apply the Sun Valley theme (Dark mode fits OBS best)
    sv_ttk.set_theme("dark")

    # Use a ttk.Frame for proper themed background and padding
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=f"New Stream Detected:\n{stream_name}\n\nRoute to OBS?", justify="center").pack(pady=(0, 15))
    
    # Use sv-ttk's built-in 'Accent' style for the primary action
    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=5)
    
    # Pack left-to-right with 5 pixels of spacing between them
    ttk.Button(button_frame, text="Yes", style="Accent.TButton", command=lambda: save_and_exit(True, True)).pack(side="left", padx=5)
    ttk.Button(button_frame, text="No", command=lambda: save_and_exit(False, False)).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Don't ask again", command=lambda: save_and_exit(False, True)).pack(side="left", padx=5)
    
    # Update layout to calculate the correct themed dimensions before moving
    root.update_idletasks()
    
    # Get the window's required width and height
    window_width = root.winfo_reqwidth()
    window_height = root.winfo_reqheight()

    # Get the screen's width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate the X and Y coordinates for the center
    center_x = int((screen_width / 2) - (window_width / 2))
    center_y = int((screen_height / 2) - (window_height / 2))

    # Apply the exact geometry (Width x Height + X_offset + Y_offset)
    root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
    
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_popup(sys.argv[1])
    else:
        run_popup("Unknown Stream")
