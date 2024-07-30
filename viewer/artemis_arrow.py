#------------------------------------------------------------------------------
# This script adds a 3D arrow object to the Unity scene and updates its position, orientation, and visibility on keyboard input.
# Press esc to stop.
#------------------------------------------------------------------------------

from pynput import keyboard
import threading
import hl2ss
import hl2ss_lnm
import hl2ss_rus
from scipy.spatial.transform import Rotation as R

# Settings --------------------------------------------------------------------
# HoloLens address
host = "192.168.2.38"

# Initial position in world space (x, y, z) in meters
position = [0, 1.6, 1]

# Initial rotation in world space (x, y, z, w) as a quaternion
rotation = R.from_quat([0, 0, 0, 1])

# Initial scale in meters
scale = [5, 5, 5]

# Movement increments
move_increment = 0.1
rotate_increment = 10  # degrees

enable = True
pointer_visible = True

stop_event = threading.Event()

def on_press(key):
    global enable, pointer_visible, position, rotation
    try:
        if key == keyboard.Key.esc:
            enable = False
            stop_event.set()
            return False
        elif key.char == 't':
            pointer_visible = not pointer_visible
        # forward, back, left, right
        elif key.char == 'w':
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
    except AttributeError:
        pass
    return True

listener = keyboard.Listener(on_press=on_press)
listener.start()

def hologram_thread():
    global enable, position, rotation, scale, pointer_visible
    ipc = hl2ss_lnm.ipc_umq(host, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)
    ipc.open()

    key = 0

    display_list = hl2ss_rus.command_buffer()
    display_list.begin_display_list()  # Begin command sequence
    display_list.remove_all()  # Remove all objects that were created remotely
    display_list.create_arrow()  # Create an arrow, server will return its id
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast)  # Set server to use the last created object as target, this avoids waiting for the id of the arrow
    display_list.set_world_transform(key, position, rotation.as_quat(), scale)  # Set the world transform of the arrow
    display_list.set_active(key, hl2ss_rus.ActiveState.Active)  # Make the arrow visible
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseID)  # Restore target mode
    display_list.end_display_list()  # End command sequence
    ipc.push(display_list)  # Send commands to server
    results = ipc.pull(display_list)  # Get results from server
    key = results[2]  # Get the arrow id, created by the 3rd command in the list

    print(f'Created arrow with id {key}')

    while enable:
        # Handle keyboard input for position and rotation
        display_list = hl2ss_rus.command_buffer()
        display_list.begin_display_list()
        display_list.set_world_transform(key, position, rotation.as_quat(), scale)
        display_list.set_active(key, hl2ss_rus.ActiveState.Active if pointer_visible else hl2ss_rus.ActiveState.Inactive)  # Set visibility
        display_list.end_display_list()
        ipc.push(display_list)
        results = ipc.pull(display_list)
        stop_event.wait(0.1)  # Short delay to avoid rapid toggling

    # Clean up
    command_buffer = hl2ss_rus.command_buffer()
    command_buffer.remove(key)
    ipc.push(command_buffer)
    results = ipc.pull(command_buffer)

    ipc.close()

# Start hologram manipulation thread
hologram_thread_instance = threading.Thread(target=hologram_thread)
hologram_thread_instance.start()

listener.join()
hologram_thread_instance.join()
