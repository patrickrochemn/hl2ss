from pynput import keyboard

import cv2
import hl2ss_imshow
import hl2ss
import hl2ss_lnm

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.38"

# Operating mode
# 0: video
# 1: video + camera pose
# 2: query calibration (single transfer)
mode = hl2ss.StreamMode.MODE_0

# Enable Mixed Reality Capture (Holograms)
enable_mrc = True

# Enable Shared Capture
shared = False

# Camera parameters
# Ignored in shared mode
width     = 1920
height    = 1080
framerate = 30

# Framerate denominator (must be > 0)
divisor = 1 

# Video encoding profile
profile = hl2ss.VideoProfile.H265_MAIN

# Decoded format
decoded_format = 'bgr24'

#------------------------------------------------------------------------------

hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, enable_mrc=enable_mrc, shared=shared)

if (mode == hl2ss.StreamMode.MODE_2):
    data = hl2ss_lnm.download_calibration_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, width, height, framerate)

else:
    enable = True

    def on_press(key):
        global enable
        enable = key != keyboard.Key.esc
        return enable

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    client = hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, mode=mode, width=width, height=height, framerate=framerate, divisor=divisor, profile=profile, decoded_format=decoded_format)
    client.open()

    while (enable):
        data = client.get_next_packet()

        cv2.imshow('Video', data.payload.image)
        cv2.waitKey(1)

    client.close()
    listener.join()

hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)