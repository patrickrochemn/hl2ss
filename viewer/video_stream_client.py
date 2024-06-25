import cv2
import numpy as np
import websocket
import threading

# WebSocket settings
ws_url = "ws://localhost:8765"  # Replace <server-ip> with your server's IP address

# Frame buffer
frame_buffer = None
lock = threading.Lock()
frame_counter = 0

def on_message(ws, message):
    global frame_buffer, frame_counter
    try:
        # Decode the received message (image frame)
        nparr = np.frombuffer(message, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Update the frame buffer
        with lock:
            frame_buffer = frame
            frame_counter += 1
    except Exception as e:
        print(f"Error processing message: {e}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket closed with code: {close_status_code}, reason: {close_msg}")

def on_open(ws):
    print("WebSocket connection opened")

def run_websocket():
    websocket.enableTrace(False)  # Disable WebSocket trace
    ws = websocket.WebSocketApp(ws_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()

# Start WebSocket in a separate thread
ws_thread = threading.Thread(target=run_websocket)
ws_thread.start()

# Display frames in an OpenCV window
while True:
    if frame_buffer is not None:
        with lock:
            frame = frame_buffer.copy()
            counter = frame_counter
        cv2.putText(frame, f"Frame: {counter}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Video Stream", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # Press 'ESC' to exit
            break

cv2.destroyAllWindows()
