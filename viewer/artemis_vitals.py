#------------------------------------------------------------------------------
# This script adds a 3D TextMeshPro object to the Unity scene and updates its text on keyboard input.
# Press esc to stop.
#------------------------------------------------------------------------------

from pynput import keyboard
import threading
import hl2ss
import hl2ss_lnm
import hl2ss_rus

# Settings --------------------------------------------------------------------

# HoloLens address
host = '192.168.2.38'

# Position in world space (x, y, z) in meters
position = [0, 1.6, 1]

# Rotation in world space (x, y, z, w) as a quaternion
rotation = [0, 0, 0, 1]

# Initial text
initial_text = 'HR: 110\nBP: 110/80\nO2: 98%'

# Font size
font_size = 0.4

# Text color
rgba = [1, 1, 1, 1]

#------------------------------------------------------------------------------

stop_event = threading.Event()

def on_press(key):
    if key == keyboard.Key.esc:
        stop_event.set()
        return False
    return True

listener = keyboard.Listener(on_press=on_press)
listener.start()

ipc = hl2ss_lnm.ipc_umq(host, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)
ipc.open()

key = 0

# Create the Interactable Text object
display_list = hl2ss_rus.command_buffer()
display_list.begin_display_list() # Begin command sequence
display_list.remove_all() # Remove all objects that were created remotely
display_list.create_interactable_text() # Create text object, server will return its id
display_list.set_target_mode(hl2ss_rus.TargetMode.UseLast) # Set server to use the last created object as target, this avoids waiting for the id of the text object
# display_list.set_text(key, font_size, rgba, initial_text) # Set text
display_list.set_world_transform(key, position, rotation, [0.05, 0.05, 0.5]) # Set the world transform of the text object
display_list.set_active(key, hl2ss_rus.ActiveState.Active) # Make the text object visible

display_list.set_target_mode(hl2ss_rus.TargetMode.UseID) # Restore target mode
display_list.end_display_list() # End command sequence
ipc.push(display_list) # Send commands to server
results = ipc.pull(display_list) # Get results from server
key = results[2] # Get the text object id, created by the 3rd command in the list

print(f'Created interactable text object with id {key}')

# Function to update the text of the created TextMeshPro object
def update_text(hr, systolic, diastolic, o2):
    new_text = f'HR: {hr}\nBP: {systolic}/{diastolic}\nO2: {o2}%'
    command_buffer = hl2ss_rus.command_buffer()
    command_buffer.begin_display_list()
    command_buffer.set_text(key, font_size, rgba, new_text) # Update the text
    command_buffer.end_display_list()
    ipc.push(command_buffer)
    ipc.pull(command_buffer)
    print(f'Updated text object with id {key} to new text: {new_text}')

# Wait for user input to update the text
def listen_for_input():
    while not stop_event.is_set():
        try:
            hr = int(input("Enter new heart rate: "))
            systolic = int(input("Enter new systolic blood pressure: "))
            diastolic = int(input("Enter new diastolic blood pressure: "))
            o2 = int(input("Enter new O2 saturation: "))
            update_text(hr, systolic, diastolic, o2)
        except Exception as e:
            print(f"Error: {e}")

input_thread = threading.Thread(target=listen_for_input)
input_thread.start()

stop_event.wait()

# Cleanup: destroy the text object
command_buffer = hl2ss_rus.command_buffer()
command_buffer.remove(key) # Destroy text object
ipc.push(command_buffer)
results = ipc.pull(command_buffer)

ipc.close()

listener.join()
input_thread.join()