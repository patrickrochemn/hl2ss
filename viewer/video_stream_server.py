import threading
import cv2
import hl2ss
import hl2ss_lnm
from websocket_server import WebsocketServer

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

# Start HoloLens video subsystem
hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, enable_mrc=True)
print("Started HoloLens video subsystem")

# Initialize video client
client = hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, mode=hl2ss.StreamMode.MODE_1, width=width, height=height, framerate=framerate, divisor=divisor, profile=profile, decoded_format=decoded_format)
client.open()

def send_video_frame(server, frame):
    ret, buffer = cv2.imencode('.jpg', frame)
    if ret:
        server.send_message_to_all(buffer.tobytes())
    else:
        print("Failed to encode frame")

def generate_frames(client, server):
    while True:
        try:
            data = client.get_next_packet()
            frame = data.payload.image
            # Send the frame over WebSocket
            send_video_frame(server, frame)
        except Exception as e:
            print(f"Error during frame generation: {e}")
            continue  # Skip this frame and continue with the next one

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

# Start generating frames and send to clients
generate_frames(client, server)

client.close()
hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)
print("Stopped HoloLens video subsystem")
