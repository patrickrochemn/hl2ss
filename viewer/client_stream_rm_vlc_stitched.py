from pynput import keyboard
import cv2
import hl2ss
import hl2ss_lnm
import numpy as np

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.38"

# Ports and labels for the cameras we are using
camera_info = [
    (hl2ss.StreamPort.RM_VLC_LEFTFRONT, "Left Front"),
    (hl2ss.StreamPort.RM_VLC_RIGHTFRONT, "Right Front")
]

# Operating mode
mode = hl2ss.StreamMode.MODE_0

# Framerate denominator
divisor = 1

# Video encoding profile
profile = hl2ss.VideoProfile.H265_MAIN

# Initialize clients for each camera
clients = []
for port, _ in camera_info:
    client = hl2ss_lnm.rx_rm_vlc(host, port, mode=mode, divisor=divisor, profile=profile)
    client.open()
    clients.append(client)

def on_press(key):
    global enable
    enable = key != keyboard.Key.esc
    return enable

# Initialize keyboard listener
enable = True
listener = keyboard.Listener(on_press=on_press)
listener.start()

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, matrix, (w, h))
    return rotated

def display_side_by_side(image1, image2):
    # Concatenate images side by side
    combined_image = np.hstack((image1, image2))
    return combined_image

while enable:
    frames = []
    for client in clients:
        data = client.get_next_packet()
        frames.append(data.payload)

    # Rotate Left Front and Right Front images
    frame_leftfront = rotate_image(frames[0], -90)  # Rotate 90 degrees counter-clockwise
    frame_rightfront = rotate_image(frames[1], 90)  # Rotate 90 degrees clockwise

    # Display Left Front and Right Front images side by side
    combined_frame = display_side_by_side(frame_leftfront, frame_rightfront)

    cv2.imshow("Left Front and Right Front Combined", combined_frame)

    cv2.waitKey(1)

# Close clients
for client in clients:
    client.close()

listener.join()
cv2.destroyAllWindows()
