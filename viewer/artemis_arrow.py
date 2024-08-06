import threading
from pynput import keyboard
import hl2ss
import hl2ss_lnm
import hl2ss_rus

# Settings --------------------------------------------------------------------
# HoloLens address
host = "192.168.2.38"

# Initial position in world space (x, y, z) in meters
position = [0, 1.6, 1]

# Initial rotation in world space (x, y, z, w) as a quaternion
rotation = [0, 0, 0, 1]

# Initial scale in meters
scale = [5, 5, 5]

enable = True
pointer_visible = True
update_needed = False

def on_press(key):
    global enable, update_needed, pointer_visible
    try:
        # Toggle pointer visibility
        if key.char == 't':
            pointer_visible = not pointer_visible
            update_needed = True
    except AttributeError:
        if key == keyboard.Key.esc:
            enable = False
            return False
    return True

listener = keyboard.Listener(on_press=on_press)
listener.start()

def hologram_thread():
    global enable, update_needed, pointer_visible
    ipc = hl2ss_lnm.ipc_umq(host, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)
    ipc.open()

    key = 0

    display_list = hl2ss_rus.command_buffer()
    display_list.begin_display_list()  # Begin command sequence
    display_list.remove_all()  # Remove all objects that were created remotely
    display_list.create_arrow()  # Create an arrow, server will return its id
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast)  # Set server to use the last created object as target, this avoids waiting for the id of the arrow
    display_list.set_world_transform(key, position, rotation, scale)  # Set the initial world transform of the arrow
    display_list.set_active(key, hl2ss_rus.ActiveState.Active)  # Make the arrow visible
    display_list.set_target_mode(hl2ss_rus.TargetMode.UseID)  # Restore target mode
    display_list.end_display_list()  # End command sequence
    ipc.push(display_list)  # Send commands to server
    results = ipc.pull(display_list)  # Get results from server
    key = results[2]  # Get the arrow id, created by the 3rd command in the list

    print(f'Created arrow with id {key}')

    while enable:
        if update_needed:
            display_list = hl2ss_rus.command_buffer()
            display_list.begin_display_list()
            display_list.toggle_object_visibility(key, pointer_visible)  # Toggle visibility
            display_list.end_display_list()
            ipc.push(display_list)
            results = ipc.pull(display_list)
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
