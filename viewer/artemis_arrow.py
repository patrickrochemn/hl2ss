import threading
from pynput import keyboard
import hl2ss
import hl2ss_lnm
import hl2ss_rus
from scipy.spatial.transform import Rotation as R

# Settings --------------------------------------------------------------------
# HoloLens address
host = "192.168.2.38"

# Initial scale in meters
scale = [5, 5, 5]

# Movement increments
move_increment = 0.1
rotate_increment = 10  # degrees

enable = True
pointer_visible = True

# Flag to indicate if an update is needed
update_needed = False

# Relative transform deltas
delta_position = [0, 0, 0]
delta_rotation = R.from_quat([0, 0, 0, 1])

def on_press(key):
    global enable, pointer_visible, update_needed, delta_position, delta_rotation
    try:
        # forward, back, left, right
        if key.char == 'w':
            delta_position[2] += move_increment
            update_needed = True
        elif key.char == 's':
            delta_position[2] -= move_increment
            update_needed = True
        elif key.char == 'a':
            delta_position[0] -= move_increment
            update_needed = True
        elif key.char == 'd':
            delta_position[0] += move_increment
            update_needed = True
        # up - y
        elif key.char == 'y':
            delta_position[1] += move_increment
            update_needed = True
        # down - h
        elif key.char == 'h':
            delta_position[1] -= move_increment
            update_needed = True
        # pitch
        elif key.char == 'i':
            delta_rotation = R.from_euler('x', -rotate_increment, degrees=True)
            update_needed = True
        elif key.char == 'k':
            delta_rotation = R.from_euler('x', rotate_increment, degrees=True)
            update_needed = True
        # yaw
        elif key.char == 'j':
            delta_rotation = R.from_euler('y', -rotate_increment, degrees=True)
            update_needed = True
        elif key.char == 'l':
            delta_rotation = R.from_euler('y', rotate_increment, degrees=True)
            update_needed = True
        # roll
        elif key.char == 'u':
            delta_rotation = R.from_euler('z', -rotate_increment, degrees=True)
            update_needed = True
        elif key.char == 'o':
            delta_rotation = R.from_euler('z', rotate_increment, degrees=True)
            update_needed = True
        # toggle pointer visibility
        elif key.char == 't':
            pointer_visible = not pointer_visible
            update_needed = True
    except AttributeError:
        if key == keyboard.Key.esc:
            enable = False
    return enable

listener = keyboard.Listener(on_press=on_press)
listener.start()

def hologram_thread():
    global enable, pointer_visible, update_needed, delta_position, delta_rotation
    ipc = hl2ss_lnm.ipc_umq(host, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)
    ipc.open()

    key = 0

    display_list = hl2ss_rus.command_buffer()
    display_list.begin_display_list()  # Begin command sequence
    display_list.remove_all()  # Remove all objects that were created remotely
    display_list.create_arrow()  # Create an arrow, server will return its id
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast)  # Set server to use the last created object as target, this avoids waiting for the id of the arrow
    display_list.set_world_transform(key, [0, 1.6, 1], [0, 0, 0, 1], scale)  # Set the initial world transform of the arrow
    display_list.set_active(key, hl2ss_rus.ActiveState.Active)  # Make the arrow visible
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseID)  # Restore target mode
    display_list.end_display_list()  # End command sequence
    ipc.push(display_list)  # Send commands to server
    results = ipc.pull(display_list)  # Get results from server
    key = results[2]  # Get the arrow id, created by the 3rd command in the list

    print(f'Created arrow with id {key}')

    while enable:
        if update_needed:
            # Apply relative changes
            display_list = hl2ss_rus.command_buffer()
            display_list.begin_display_list()
            display_list.set_arrow_transform(key, delta_position, delta_rotation.as_quat(), [0, 0, 0])  # Use [0, 0, 0] for scale change to keep it consistent
            display_list.set_active(key, hl2ss_rus.ActiveState.Active if pointer_visible else hl2ss_rus.ActiveState.Inactive)  # Set visibility
            display_list.end_display_list()
            ipc.push(display_list)
            results = ipc.pull(display_list)
            
            # Reset deltas
            delta_position = [0, 0, 0]
            delta_rotation = R.from_quat([0, 0, 0, 1])
            update_needed = False

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
