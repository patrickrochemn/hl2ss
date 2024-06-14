import asyncio
import websockets
from pynput import keyboard
import cv2
import hl2ss
import hl2ss_lnm

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.39"

# Operating mode
mode = hl2ss.StreamMode.MODE_1

# Enable Mixed Reality Capture (Holograms)
enable_mrc = True

# Camera parameters
width = 1920
height = 1080
framerate = 30

# Framerate denominator (must be > 0)
divisor = 1 

# Video encoding profile
profile = hl2ss.VideoProfile.H265_MAIN

# Decoded format
decoded_format = 'bgr24'

# WebSocket settings
ws_host = "localhost"
ws_port = 8765

#------------------------------------------------------------------------------

hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, enable_mrc=enable_mrc)

if mode == hl2ss.StreamMode.MODE_2:
    data = hl2ss_lnm.download_calibration_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, width, height, framerate)
else:
    enable = True

    def on_press(key):
        global enable
        enable = key != keyboard.Key.esc
        return enable

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    client = hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, mode=mode, width=width, height=height, framerate=framerate, divisor=divisor, profile=profile, decoded_format=decoded_format)
    client.open()

    async def send_video_frame(websocket, path):
        global enable
        try:
            while enable:
                data = client.get_next_packet()
                frame = data.payload.image
                _, buffer = cv2.imencode('.jpg', frame)
                await websocket.send(buffer.tobytes())
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await websocket.close()

    async def main():
        async with websockets.serve(send_video_frame, ws_host, ws_port):
            print(f"WebSocket server started at ws://{ws_host}:{ws_port}")
            await asyncio.Future()  # run forever

    asyncio.run(main())

    client.close()
    listener.join()

hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)
