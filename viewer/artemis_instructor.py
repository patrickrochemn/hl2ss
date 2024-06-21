import threading
from pynput import keyboard
import cv2
import hl2ss
import hl2ss_lnm
import hl2ss_rus
from websocket_server import WebsocketServer
from scipy.spatial.transform import Rotation as R

# Settings --------------------------------------------------------------------
# HoloLens address
host = "192.168.2.39"

# Camera parameters
width = 1920
height = 1080
framerate = 30

# Framerate denominator (must be > 0). Effective FPS is framerate / divisor
divisor = 1 

# Video encoding profile
profile = hl2ss.VideoProfile.H265_MAIN

# Decoded format
decoded_format = 'bgr24'

# WebSocket settings
ws_port = 8765

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

enable = True
pointer_visible = True

# Start HoloLens video subsystem
hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, enable_mrc=True)
print("Started HoloLens video subsystem")

# Initialize video client
client = hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, mode=hl2ss.StreamMode.MODE_1, width=width, height=height, framerate=framerate, divisor=divisor, profile=profile, decoded_format=decoded_format)
client.open()

def send_video_frame(client, server, frame):
    ret, buffer = cv2.imencode('.jpg', frame)
    server.send_message_to_all(buffer.tobytes())

def generate_frames(client, server):
    while True:
        try:
            data = client.get_next_packet()
            frame = data.payload.image
            # Send the frame over WebSocket
            send_video_frame(client, server, frame)
        except Exception as e:
            print(f"Error during frame generation: {e}")
            break

# WebSocket event handlers
def new_client(client, server):
    print(f"New client connected and was given id {client['id']}")

def client_left(client, server):
    print(f"Client({client['id']}) disconnected")

def message_received(client, server, message):
    print(f"Client({client['id']}) said: {message}")

# Create WebSocket server
server = WebsocketServer(host='0.0.0.0', port=ws_port)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)

# Modify the send_message method to handle binary data
def send_message_binary(client, data):
    header = bytearray([0x82])
    length = len(data)
    if length <= 125:
        header.append(length)
    elif length >= 126 and length <= 65535:
        header.append(126)
        header += length.to_bytes(2, 'big')
    else:
        header.append(127)
        header += length.to_bytes(8, 'big')
    client['handler'].request.sendall(header + data)

server.send_message_to_all = lambda data: [send_message_binary(client, data) for client in server.clients]

# Start WebSocket server in a separate thread
ws_thread = threading.Thread(target=server.run_forever)
ws_thread.start()

# Hologram manipulation thread
def hologram_thread():
    global enable, pointer_visible
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

    def on_press(key):
        global enable, position, rotation, pointer_visible
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
            # toggle pointer visibility
            elif key.char == 't':
                pointer_visible = not pointer_visible
        except AttributeError:
            if key == keyboard.Key.esc:
                enable = False
        return enable

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    while enable:
        display_list = hl2ss_rus.command_buffer()
        display_list.begin_display_list()
        display_list.set_world_transform(key, position, rotation.as_quat(), scale)
        display_list.set_active(key, hl2ss_rus.ActiveState.Active if pointer_visible else hl2ss_rus.ActiveState.Inactive)  # Set visibility
        display_list.end_display_list()
        ipc.push(display_list)
        results = ipc.pull(display_list)

    # Clean up
    command_buffer = hl2ss_rus.command_buffer()
    command_buffer.remove(key)
    ipc.push(command_buffer)
    results = ipc.pull(command_buffer)

    ipc.close()

# Start hologram manipulation thread
hologram_thread = threading.Thread(target=hologram_thread)
hologram_thread.start()

# Start generating frames and send to clients
generate_frames(client, server)

client.close()
hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)
print("Stopped HoloLens video subsystem")
