import threading
import cv2
import hl2ss
import hl2ss_lnm

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

def stream_vlc_camera(port, name, window_name):
    client = hl2ss_lnm.rx_rm_vlc(host, port, vlc_mode)
    client.open()
    while True:
        try:
            data = client.get_next_packet()
            frame = data.payload
            with frame_lock:
                frames[name] = frame

            # Ensure VLC frames have 3 dimensions
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            cv2.imshow(window_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"Error in {name}: {e}")
            break
    client.close()
    cv2.destroyAllWindows()

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

            cv2.imshow('RGB Camera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_streaming()
                break
        except Exception as e:
            print(f"Error in RGB stream: {e}")
            break
    client.close()
    hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)
    cv2.destroyAllWindows()

def stop_streaming():
    global running
    running = False
    cv2.destroyAllWindows()

# Start threads for VLC and RGB cameras
threads = []
for i, port in enumerate(vlc_ports):
    t = threading.Thread(target=stream_vlc_camera, args=(port, f'vlc_{["left", "right"][i]}', f'VLC {["Left", "Right"][i]} Camera'))
    t.start()
    threads.append(t)

rgb_thread = threading.Thread(target=stream_rgb_camera)
rgb_thread.start()
threads.append(rgb_thread)

# Wait for all threads to finish
for t in threads:
    t.join()
