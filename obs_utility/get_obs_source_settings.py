import obsws_python as obs
from dotenv import load_dotenv
import os

load_dotenv()

cl = obs.ReqClient(host='localhost', port=4455, password=os.getenv('OBS_PASSWORD'))

SOURCE_NAME = "Game Audio"

def print_source_settings(source_name=SOURCE_NAME):
    try:
        response = cl.get_input_settings(source_name)
        print("\n--- OBS Settings for '{}' ---".format(source_name))
        for key, value in response.input_settings.items():
            print(f"Key: '{key}' | Value: {value} | Type: {type(value)}")
        print("----------------------------------\n")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print_source_settings()
