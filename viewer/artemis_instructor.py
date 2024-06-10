import threading
from pynput import keyboard
import cv2
import hl2ss_imshow
import hl2ss
import hl2ss_lnm
import hl2ss_rus
from scipy.spatial.transform import Rotation as R
import numpy as np

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
rotation = R.from_quat([0, 0, 0, 1])

# Initial scale in meters
scale = [0.2, 0.2, 0.2]

# Initial color
rgba = [0, 1, 0, 1]

# Movement increments
move_increment = 0.1
rotate_increment = 10  # degrees

#------------------------------------------------------------------------------

enable = True
cube_visible = True

def on_press(key):
    global enable, position, rotation, cube_visible
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
            rotation *= R.from_euler('x', -rotate_increment, degrees=True)
        elif key.char == 'k':
            rotation *= R.from_euler('x', rotate_increment, degrees=True)
        # yaw
        elif key.char == 'j':
            rotation *= R.from_euler('y', -rotate_increment, degrees=True)
        elif key.char == 'l':
            rotation *= R.from_euler('y', rotate_increment, degrees=True)
        # roll
        elif key.char == 'u':
            rotation *= R.from_euler('z', -rotate_increment, degrees=True)
        elif key.char == 'o':
            rotation *= R.from_euler('z', rotate_increment, degrees=True)
        # toggle cube visibility
        elif key.char == 't':
            cube_visible = not cube_visible
    except AttributeError:
        if key == keyboard.Key.esc:
            enable = False
    return enable

# Thread function for hologram manipulation
def hologram_thread():
    global enable, cube_visible
    ipc = hl2ss_lnm.ipc_umq(host, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)
    ipc.open()

    key = 0

    display_list = hl2ss_rus.command_buffer()
    display_list.begin_display_list()  # Begin command sequence
    display_list.remove_all()  # Remove all objects that were created remotely
    display_list.create_primitive(hl2ss_rus.PrimitiveType.Cube)  # Create a cube, server will return its id
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast)  # Set server to use the last created object as target, this avoids waiting for the id of the cube
    display_list.set_world_transform(key, position, rotation.as_quat(), scale)  # Set the world transform of the cube
    display_list.set_color(key, rgba)  # Set the color of the cube
    display_list.set_active(key, hl2ss_rus.ActiveState.Active)  # Make the cube visible
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseID)  # Restore target mode
    display_list.end_display_list()  # End command sequence
    ipc.push(display_list)  # Send commands to server
    results = ipc.pull(display_list)  # Get results from server
    key = results[2]  # Get the cube id, created by the 3rd command in the list

    print(f'Created cube with id {key}')

    while enable:
        display_list = hl2ss_rus.command_buffer()
        display_list.begin_display_list()
        display_list.set_world_transform(key, position, rotation.as_quat(), scale)
        display_list.set_active(key, hl2ss_rus.ActiveState.Active if cube_visible else hl2ss_rus.ActiveState.Inactive)  # Set visibility
        display_list.end_display_list()
        ipc.push(display_list)
        results = ipc.pull(display_list)
    
    # Clean up
    command_buffer = hl2ss_rus.command_buffer()
    command_buffer.remove(key)
    ipc.push(command_buffer)
    resultes = ipc.pull(command_buffer)

    ipc.close()

# Thread function for video streaming
def video_stream_thread():
    global enable
    hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, enable_mrc=enable_mrc)

    if mode == hl2ss.StreamMode.MODE_2:
        data = hl2ss_lnm.download_calibration_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, width, height, framerate)
    else:
        client = hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, mode=mode, width=width, height=height, framerate=framerate, divisor=divisor, profile=profile, decoded_format=decoded_format)
        client.open()

        while enable:
            try:
                data = client.get_next_packet()
                cv2.imshow('Video', data.payload.image)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
            except Exception as e:
                print(f"Error: {e}")
                break

        client.close()

    hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)

# Main execution
if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    hologram_thread = threading.Thread(target=hologram_thread)
    video_stream_thread = threading.Thread(target=video_stream_thread)

    hologram_thread.start()
    video_stream_thread.start()

    hologram_thread.join()
    video_stream_thread.join()

    listener.join()
    cv2.destroyAllWindows()