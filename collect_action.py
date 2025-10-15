# collect_my_dataset.py (Robust Version)

import pyrealsense2 as rs
import time
import os


SERIAL_NUMBER_1 = '832112070255'
SERIAL_NUMBER_2 = '213622078112'
WIDTH, HEIGHT, FRAMERATE = 640, 480, 15
RECORDING_DURATION_SECONDS = 5
DATASET_DIR = "Dataset"
ACTION_POOL = {
    1: "Approaching",
    2: "Grasping",
    3: "Transporting",
    4: "Releasing",
    5: "Idle/Resting"
}

def get_next_take_number(action_path):
    os.makedirs(action_path, exist_ok=True)
    # Check for files from the first camera to determine the take number
    takes = [f for f in os.listdir(action_path) if f.startswith('take_') and f.endswith(f'_{SERIAL_NUMBER_1}.bag')]
    if not takes: return 1
    max_num = max([int(t.split('_')[1]) for t in takes])
    return max_num + 1

def print_menu():
    print("\n" + "="*50 + "\n           CHOOSE AN ACTION TO RECORD\n" + "="*50)
    for key, value in ACTION_POOL.items(): print(f"  [{key:2d}] {value}")
    print("\n  [q] Quit\n" + "="*50)

def main():
    if SERIAL_NUMBER_1 == '000000000000' or SERIAL_NUMBER_2 == '000000000000':
        print("\nERROR: PLEASE REPLACE THE PLACEHOLDER SERIAL NUMBERS!\n")
        return
        
    ctx = rs.context()
    if len(ctx.query_devices()) < 2:
        print("Error: Two RealSense cameras are required."); return

    pipeline_1, pipeline_2 = rs.pipeline(ctx), rs.pipeline(ctx)
    config_1, config_2 = rs.config(), rs.config()

    try:
        config_1.enable_device(SERIAL_NUMBER_1)
        config_2.enable_device(SERIAL_NUMBER_2)
        for cfg in [config_1, config_2]:
            cfg.enable_stream(rs.stream.depth, WIDTH, HEIGHT, rs.format.z16, FRAMERATE)
            cfg.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, FRAMERATE)

        while True:
            print_menu()
            choice = input("Enter the number of the action: ")
            if choice.lower() == 'q': break
            
            try:
                action_name = ACTION_POOL[int(choice)]
            except (ValueError, KeyError):
                print("!!! Invalid choice, please try again. !!!"); continue

            action_path = os.path.join(DATASET_DIR, action_name)
            take_number = get_next_take_number(action_path)
            
            print(f"\n---> Preparing for action: '{action_name}', take number: {take_number}")

            # --- MODIFIED: Define separate output files ---
            base_filename = os.path.join(action_path, f"take_{take_number:02d}")
            output_filename_1 = f"{base_filename}_{SERIAL_NUMBER_1}.bag"
            output_filename_2 = f"{base_filename}_{SERIAL_NUMBER_2}.bag"
            
            config_1.enable_record_to_file(output_filename_1)
            config_2.enable_record_to_file(output_filename_2)

            print("Ready...", end="", flush=True); time.sleep(1)
            print(" Set...", end="", flush=True); time.sleep(1)
            print(" GO!")
            
            pipeline_1.start(config_1)
            pipeline_2.start(config_2)
            
            print(f"🔴 RECORDING for {RECORDING_DURATION_SECONDS} seconds...")
            time.sleep(RECORDING_DURATION_SECONDS)
            
            print("⏹️ Stopping recording...")
            pipeline_1.stop()
            pipeline_2.stop()
            print(f"Recordings saved successfully.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("\nData collection finished. Exiting program.")

if __name__ == '__main__':
    main()