#------------------------------------------------------------------------------
# This script receives video from the HoloLens front RGB camera as well as
# holograms and plays it. It also can display and manipulate a 3D cube.
# The camera supports various resolutions and framerates. See
# https://github.com/jdibenes/hl2ss/blob/main/etc/pv_configurations.txt
# for a list of supported formats. The default configuration is 1080p 30 FPS. 
# The stream supports three operating modes: 0) video, 1) video + camera pose, 
# 2) query calibration (single transfer).
# Press esc to stop.
#------------------------------------------------------------------------------

from pynput import keyboard

import cv2
import hl2ss_imshow
import hl2ss
import hl2ss_lnm
import hl2ss_rus

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.39"

# Operating mode
# 0: video
# 1: video + camera pose
# 2: query calibration (single transfer)
mode = hl2ss.StreamMode.MODE_1

# Enable Mixed Reality Capture (Holograms)
enable_mrc = True

# Camera parameters
width     = 1280
height    = 720
framerate = 30

# Framerate denominator (must be > 0)
# Effective FPS is framerate / divisor
divisor = 1 

# Video encoding profile
profile = hl2ss.VideoProfile.H265_MAIN

# Decoded format
# Options include: 'bgr24','rgb24','bgra','rgba','gray8'
decoded_format = 'bgr24'

# Cube parameters -------------------------------------------------------------

# Initial position in world space (x, y, z) in meters
position = [0, 1.6, 1]

# Initial rotation in world space (x, y, z, w) as a quaternion
rotation = [0, 0, 0, 1]

# Initial scale in meters
scale = [0.2, 0.2, 0.2]

# Initial color
rgba = [0, 1, 0, 1]

# Movement increments
move_increment = 0.1
rotate_increment = 10  # degrees

#------------------------------------------------------------------------------

enable = True

def on_press(key):
    global enable, position, rotation
    try:
        # print(f'key {key.char} pressed')
        # forward, back, left, right
        if key.char == 'w':
            position[2] += move_increment
        elif key.char == 's':
            position[2] -= move_increment
        elif key.char == 'a':
            position[0] -= move_increment
        elif key.char == 'd':
            position[0] += move_increment
        # up - y
        elif key.char == 'y':
            position[1] += move_increment
        # down - h
        elif key.char == 'h':
            position[1] -= move_increment
        # pitch, yaw, and roll are a bit more complex because they are quaternions
        # pitch
        elif key.char == 'i':
            rotation[0] -= rotate_increment
        elif key.char == 'k':
            rotation[0] += rotate_increment
        # yaw
        elif key.char == 'j':
            rotation[1] -= rotate_increment
        elif key.char == 'l':
            rotation[1] += rotate_increment
        # roll
        elif key.char == 'u':
            rotation[2] -= rotate_increment
        elif key.char == 'o':
            rotation[2] += rotate_increment
    except AttributeError:
        if key == keyboard.Key.esc:
            enable = False
    return enable

listener = keyboard.Listener(on_press=on_press)
listener.start()

ipc = hl2ss_lnm.ipc_umq(host, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)
ipc.open()

key = 0

display_list = hl2ss_rus.command_buffer()
display_list.begin_display_list() # Begin command sequence
display_list.remove_all() # Remove all objects that were created remotely
display_list.create_primitive(hl2ss_rus.PrimitiveType.Cube) # Create a cube, server will return its id
display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast) # Set server to use the last created object as target, this avoids waiting for the id of the cube
display_list.set_world_transform(key, position, rotation, scale) # Set the world transform of the cube
display_list.set_color(key, rgba) # Set the color of the cube
display_list.set_active(key, hl2ss_rus.ActiveState.Active) # Make the cube visible
display_list.set_target_mode(hl2ss_rus.TargetMode.UseID) # Restore target mode
display_list.end_display_list() # End command sequence
ipc.push(display_list) # Send commands to server
results = ipc.pull(display_list) # Get results from server
key = results[2] # Get the cube id, created by the 3rd command in the list

print(f'Created cube with id {key}')

hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, enable_mrc=enable_mrc)

if (mode == hl2ss.StreamMode.MODE_2):
    data = hl2ss_lnm.download_calibration_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, width, height, framerate)
else:
    client = hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, mode=mode, width=width, height=height, framerate=framerate, divisor=divisor, profile=profile, decoded_format=decoded_format)
    client.open()

    while (enable):
        display_list = hl2ss_rus.command_buffer()
        display_list.begin_display_list()
        display_list.set_world_transform(key, position, rotation, scale)
        display_list.end_display_list()
        ipc.push(display_list)
        results = ipc.pull(display_list)

        data = client.get_next_packet()

        cv2.imshow('Video', data.payload.image)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Clean up
    client.close()
    command_buffer = hl2ss_rus.command_buffer()
    command_buffer.remove(key) # Destroy cube
    ipc.push(command_buffer)
    results = ipc.pull(command_buffer)

ipc.close()

listener.join()

hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)
