# process_parallel.py

import pyrealsense2 as rs
import numpy as np
import cv2
import os
import concurrent.futures
from tqdm import tqdm

# ======================================================================================
# --- 1. Configuration - MUST BE EDITED ---
# ======================================================================================
SERIAL_NUMBER_1 = '000000000000'  # <-- REPLACE THIS (e.g., Top-down camera)
SERIAL_NUMBER_2 = '000000000000'  # <-- REPLACE THIS (e.g., Side-view camera)
WIDTH, HEIGHT = 640, 480
FPS = 15 # <-- IMPORTANT: This must match the FPS you used for recording!

BASE_DATASET_DIR = "Dataset"
OUTPUT_DIR_BASE = "Dataset_Extracted"

# --- [NEW] Concurrency Settings ---
# Uses all available CPU cores by default. You can set a specific number, e.g., 4.
MAX_WORKERS = os.cpu_count()
# ======================================================================================

def process_take(action_name, take_number):
    """
    This is the "worker" function. It processes a single pair of .bag files for one take.
    It's designed to be run in its own process.
    """
    base_filename = f"take_{take_number:02d}"
    input_bag_1 = os.path.join(BASE_DATASET_DIR, action_name, f"{base_filename}_{SERIAL_NUMBER_1}.bag")
    input_bag_2 = os.path.join(BASE_DATASET_DIR, action_name, f"{base_filename}_{SERIAL_NUMBER_2}.bag")

    if not os.path.exists(input_bag_1) or not os.path.exists(input_bag_2):
        return f"Skipped take {take_number:02d}: one or both .bag files are missing."

    output_path = os.path.join(OUTPUT_DIR_BASE, action_name, f"take_{take_number:02d}")
    paths_to_create = { "cam1_color": os.path.join(output_path, "cam1_color"), "cam1_depth": os.path.join(output_path, "cam1_depth"), "cam2_color": os.path.join(output_path, "cam2_color"), "cam2_depth": os.path.join(output_path, "cam2_depth")}
    for path in paths_to_create.values(): os.makedirs(path, exist_ok=True)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    merged_rgb_path = os.path.join(OUTPUT_DIR_BASE, action_name, f"{action_name}_take_{take_number:02d}_merged_rgb.mov")
    merged_depth_path = os.path.join(OUTPUT_DIR_BASE, action_name, f"{action_name}_take_{take_number:02d}_merged_depth.mov")
    rgb_writer = cv2.VideoWriter(merged_rgb_path, fourcc, FPS, (WIDTH * 2, HEIGHT))
    depth_writer = cv2.VideoWriter(merged_depth_path, fourcc, FPS, (WIDTH * 2, HEIGHT))

    pipeline1, pipeline2 = rs.pipeline(), rs.pipeline()
    config1, config2 = rs.config(), rs.config()
    rs.config.enable_device_from_file(config1, input_bag_1, repeat_playback=False)
    rs.config.enable_device_from_file(config2, input_bag_2, repeat_playback=False)

    try:
        pipeline1.start(config1).get_device().as_playback().set_real_time(False)
        pipeline2.start(config2).get_device().as_playback().set_real_time(False)
    except RuntimeError as e:
        return f"ERROR processing take {take_number:02d}: {e}. Skipping."

    align = rs.align(rs.stream.color)
    frame_count = 0
    try:
        while True:
            success1, frames1 = pipeline1.try_wait_for_frames(100)
            success2, frames2 = pipeline2.try_wait_for_frames(100)
            if not success1 or not success2: break

            aligned_frames1, aligned_frames2 = align.process(frames1), align.process(frames2)
            color_frame1, depth_frame1 = aligned_frames1.get_color_frame(), aligned_frames1.get_depth_frame()
            color_frame2, depth_frame2 = aligned_frames2.get_color_frame(), aligned_frames2.get_depth_frame()

            if not all([color_frame1, depth_frame1, color_frame2, depth_frame2]): continue

            color1, depth1 = np.asanyarray(color_frame1.get_data()), np.asanyarray(depth_frame1.get_data())
            color2, depth2 = np.asanyarray(color_frame2.get_data()), np.asanyarray(depth_frame2.get_data())

            # Write RGB
            rgb_writer.write(np.hstack((color1, color2)))
            # Write Depth
            depth_colormap1 = cv2.applyColorMap(cv2.convertScaleAbs(depth1, alpha=0.03), cv2.COLORMAP_JET)
            depth_colormap2 = cv2.applyColorMap(cv2.convertScaleAbs(depth2, alpha=0.03), cv2.COLORMAP_JET)
            depth_writer.write(np.hstack((depth_colormap1, depth_colormap2)))

            # Save raw PNGs
            cv2.imwrite(os.path.join(paths_to_create["cam1_color"], f"frame_{frame_count:04d}.png"), color1)
            cv2.imwrite(os.path.join(paths_to_create["cam2_color"], f"frame_{frame_count:04d}.png"), color2)
            cv2.imwrite(os.path.join(paths_to_create["cam1_depth"], f"frame_{frame_count:04d}.png"), depth1.astype(np.uint16))
            cv2.imwrite(os.path.join(paths_to_create["cam2_depth"], f"frame_{frame_count:04d}.png"), depth2.astype(np.uint16))
            
            frame_count += 1
    finally:
        pipeline1.stop()
        pipeline2.stop()
        rgb_writer.release()
        depth_writer.release()
    
    return f"Processed take {take_number:02d} ({frame_count} frames)"

def main():
    """
    The "manager" function. It finds all takes and distributes them
    to a pool of worker processes.
    """
    if SERIAL_NUMBER_1 == '000000000000' or SERIAL_NUMBER_2 == '000000000000':
        print("\nERROR: PLEASE REPLACE THE PLACEHOLDER SERIAL NUMBERS IN THE SCRIPT!\n"); return
    
    if not os.path.isdir(BASE_DATASET_DIR): print(f"Error: Dataset directory '{BASE_DATASET_DIR}' not found."); return

    # --- 1. Create a list of all jobs to be done ---
    tasks = []
    action_names = sorted([d for d in os.listdir(BASE_DATASET_DIR) if os.path.isdir(os.path.join(BASE_DATASET_DIR, d))])
    
    for action_name in action_names:
        action_path = os.path.join(BASE_DATASET_DIR, action_name)
        take_numbers = set()
        for filename in os.listdir(action_path):
            if filename.startswith('take_') and f'_{SERIAL_NUMBER_1}.bag' in filename:
                try: take_numbers.add(int(filename.split('_')[1]))
                except (IndexError, ValueError): pass
        
        for take_number in sorted(list(take_numbers)):
            tasks.append((action_name, take_number))

    if not tasks:
        print("No takes found to process."); return

    # --- 2. Create a Process Pool and execute jobs in parallel ---
    print(f"Found {len(tasks)} takes to process. Starting parallel processing with {MAX_WORKERS} workers...")
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # The 'map' function distributes the tasks to the worker processes.
        # 'tqdm' wraps this to create a live progress bar.
        results = list(tqdm(executor.map(lambda p: process_take(*p), tasks), total=len(tasks)))
    
    print(f"\n{'='*60}\nDataset processing complete.\n{'='*60}")
    # Optional: Print results for a summary
    # for res in results:
    #     print(res)

if __name__ == '__main__':
    # This check is CRITICAL for multiprocessing to work correctly
    main()