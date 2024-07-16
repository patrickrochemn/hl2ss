#------------------------------------------------------------------------------
# This script receives video from multiple HoloLens sideview grayscale
# cameras and stitches them into one large frame. The camera resolution is 
# 640x480 @ 30 FPS. The stream supports three operating modes: 0) video, 
# 1) video + rig pose, 2) query calibration (single transfer).
# Press esc to stop.
#------------------------------------------------------------------------------

from pynput import keyboard
import cv2
import numpy as np
import hl2ss
import hl2ss_lnm

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.38"

# Ports for multiple cameras
ports = [
    hl2ss.StreamPort.RM_VLC_LEFTFRONT,
    hl2ss.StreamPort.RM_VLC_RIGHTFRONT,
    hl2ss.StreamPort.RM_VLC_LEFTLEFT,
    hl2ss.StreamPort.RM_VLC_RIGHTRIGHT
]

# Operating mode
# 0: video
# 1: video + rig pose
# 2: query calibration (single transfer)
mode = hl2ss.StreamMode.MODE_0

# Framerate denominator (must be > 0)
# Effective framerate is framerate / divisor
divisor = 1

# Video encoding profile
profile = hl2ss.VideoProfile.H265_MAIN

#------------------------------------------------------------------------------

def on_press(key):
    global enable
    enable = key != keyboard.Key.esc
    return enable

# Initialize keyboard listener
enable = True
listener = keyboard.Listener(on_press=on_press)
listener.start()

# Initialize clients for each camera
clients = []
for port in ports:
    client = hl2ss_lnm.rx_rm_vlc(host, port, mode=mode, divisor=divisor, profile=profile)
    client.open()
    clients.append(client)

while enable:
    frames = []
    for client in clients:
        data = client.get_next_packet()
        frames.append(data.payload)

    # Assuming the frames are 640x480, create a blank image to stitch frames
    if len(frames) == 4:
        top_row = np.hstack((frames[2], frames[0]))  # Left-left and Left-front
        bottom_row = np.hstack((frames[1], frames[3]))  # Right-front and Right-right
        stitched_frame = np.vstack((top_row, bottom_row))
    elif len(frames) == 2:
        stitched_frame = np.hstack((frames[0], frames[1]))
    else:
        stitched_frame = frames[0]

    cv2.imshow('Stitched Video', stitched_frame)
    cv2.waitKey(1)

# Close clients
for client in clients:
    client.close()

listener.join()
cv2.destroyAllWindows()
