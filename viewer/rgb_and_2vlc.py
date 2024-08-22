import threading
import cv2
import hl2ss
import hl2ss_lnm
import numpy as np

# Settings
host = "192.168.2.38"

# Stream settings for VLC cameras
vlc_ports = [hl2ss.StreamPort.RM_VLC_LEFTFRONT, hl2ss.StreamPort.RM_VLC_RIGHTFRONT]
vlc_mode = hl2ss.StreamMode.MODE_1

# Stream settings for RGB camera
rgb_mode = hl2ss.StreamMode.MODE_0
width = 1920
height = 1080
framerate = 30
profile = hl2ss.VideoProfile.H265_MAIN
decoded_format = 'bgr24'

# Global variables for frames
frames = {'vlc_left': None, 'vlc_right': None, 'rgb': None}

# Lock for thread-safe access to frames
frame_lock = threading.Lock()

def stream_vlc_camera(port, name):
    client = hl2ss_lnm.rx_rm_vlc(host, port, vlc_mode)
    client.open()
    while True:
        try:
            data = client.get_next_packet()
            frame = data.payload
            with frame_lock:
                frames[name] = frame
        except Exception as e:
            print(f"Error in {name}: {e}")
            break
    client.close()

def stream_rgb_camera():
    hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)
    client = hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, mode=rgb_mode, width=width, height=height, framerate=framerate, profile=profile, decoded_format=decoded_format)
    client.open()
    while True:
        try:
            data = client.get_next_packet()
            frame = data.payload.image
            with frame_lock:
                frames['rgb'] = frame
        except Exception as e:
            print(f"Error in RGB stream: {e}")
            break
    client.close()
    hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)

def display_frames():
    while True:
        with frame_lock:
            vlc_left = frames['vlc_left']
            vlc_right = frames['vlc_right']
            rgb = frames['rgb']

        if vlc_left is not None and vlc_right is not None and rgb is not None:
            # Ensure VLC frames have 3 dimensions
            if len(vlc_left.shape) == 2:
                vlc_left = cv2.cvtColor(vlc_left, cv2.COLOR_GRAY2BGR)
            if len(vlc_right.shape) == 2:
                vlc_right = cv2.cvtColor(vlc_right, cv2.COLOR_GRAY2BGR)

            # Resize frames to fit in a 2x2 grid
            vlc_left_resized = cv2.resize(vlc_left, (width // 2, height // 2))
            vlc_right_resized = cv2.resize(vlc_right, (width // 2, height // 2))
            rgb_resized = cv2.resize(rgb, (width, height // 2))

            # Combine frames
            top_row = rgb_resized
            bottom_row = np.hstack((vlc_left_resized, vlc_right_resized))
            combined_frame = np.vstack((top_row, bottom_row))

            cv2.imshow('Combined Video Feed', combined_frame)
            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

# Start threads for VLC and RGB cameras
threads = []
for i, port in enumerate(vlc_ports):
    t = threading.Thread(target=stream_vlc_camera, args=(port, f'vlc_{["left", "right"][i]}'))
    t.start()
    threads.append(t)

rgb_thread = threading.Thread(target=stream_rgb_camera)
rgb_thread.start()
threads.append(rgb_thread)

# Start the display thread
display_thread = threading.Thread(target=display_frames)
display_thread.start()

# Wait for all threads to finish
for t in threads:
    t.join()
display_thread.join()
