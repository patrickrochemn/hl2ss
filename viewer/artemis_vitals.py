import threading
from pynput import keyboard
import hl2ss
import hl2ss_lnm
import hl2ss_rus

# Settings --------------------------------------------------------------------

# HoloLens address
host = '192.168.2.39'

# Initial text content
text_content = "Artemis"

#------------------------------------------------------------------------------

stop_event = threading.Event()

def on_press(key):
    if key == keyboard.Key.esc:
        stop_event.set()
        return False
    elif key.char == 'v':  # Toggle text visibility
        toggle_text_visibility()
    return True

def toggle_text_visibility():
    global text_visible
    text_visible = not text_visible
    ipc.command("ToggleTextDisplay", "true" if text_visible else "false")

listener = keyboard.Listener(on_press=on_press)
listener.start()

ipc = hl2ss_lnm.ipc_umq(host, hl2ss.IPCPort.UNITY_MESSAGE_QUEUE)
ipc.open()

# Initial command to set the text content
ipc.command("SetTextDisplayContent", text_content)

stop_event.wait()

ipc.close()
listener.join()
