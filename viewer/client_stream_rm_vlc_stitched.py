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

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, matrix, (w, h))
    return rotated

while enable:
    frames = []
    for client in clients:
        data = client.get_next_packet()
        frames.append(data.payload)

    # Rotate frames as specified
    frame_leftfront = rotate_image(frames[0], -90)  # Top-left
    frame_rightfront = rotate_image(frames[1], 90)  # Top-right
    frame_leftleft = rotate_image(frames[2], 90)  # Bottom-left
    frame_rightright = rotate_image(frames[3], -90)  # Bottom-right (corrected)

    # Stitch frames together
    top_row = np.hstack((frame_leftleft, frame_leftfront))
    bottom_row = np.hstack((frame_rightfront, frame_rightright))
    stitched_frame = np.vstack((top_row, bottom_row))

    cv2.imshow('Stitched Video', stitched_frame)
    cv2.waitKey(1)

# Close clients
for client in clients:
    client.close()

listener.join()
cv2.destroyAllWindows()
