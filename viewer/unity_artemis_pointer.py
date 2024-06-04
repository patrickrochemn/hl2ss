#------------------------------------------------------------------------------
# This script adds an arrow pointer to the Unity scene and allows control using keyboard input.
# Press esc to stop.
#------------------------------------------------------------------------------

from pynput import keyboard
import hl2ss
import hl2ss_lnm
import hl2ss_rus

# Settings --------------------------------------------------------------------

# HoloLens address
host = '192.168.2.39'

# Initial position in world space (x, y, z) in meters
position = [0, 1.6, 1]

# Initial rotation in world space (x, y, z, w) as a quaternion
rotation = [0, 0, 0, 1]

# Initial scale in meters
scale = [0.2, 0.2, 0.2]

# Initial color
rgba = [0, 0, 1, 1]

# Movement increments
move_increment = 0.1
rotate_increment = 10  # degrees

#------------------------------------------------------------------------------

enable = True

def on_press(key):
    global enable
    try:
        print(f'key {key.char} pressed')
        # forward, back, left, right
        if key.char == 'w':
            position[2] += move_increment
        elif key.char == 's':
            position[2] -= move_increment
        elif key.char == 'a':
            position[0] -= move_increment
        elif key.char == 'd':
            position[0] += move_increment
        # up - space bar
        elif key.char == 'y':
            position[1] += move_increment
        # down - ctrl
        elif key.char == 'h':
            position[1] -= move_increment
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

while enable:
    display_list = hl2ss_rus.command_buffer()
    display_list.begin_display_list()
    display_list.set_world_transform(key, position, rotation, scale)
    display_list.end_display_list()
    ipc.push(display_list)
    results = ipc.pull(display_list)

# Clean up
command_buffer = hl2ss_rus.command_buffer()
command_buffer.remove(key) # Destroy cube
ipc.push(command_buffer)
results = ipc.pull(command_buffer)

ipc.close()

listener.join()
