import cv2
import hl2ss
import hl2ss_lnm

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.38"

# Configure stream ports for the RGB camera
stream_port_rgb = hl2ss.StreamPort.PERSONAL_VIDEO

# Frame dimensions
rgb_width, rgb_height = 1280, 720

# Other configurations
framerate = 30  # Adjust based on your needs

#------------------------------------------------------------------------------

def stream_rgb_camera():
    client = hl2ss_lnm.rx_pv(host, stream_port_rgb, mode=hl2ss.StreamMode.MODE_0, width=rgb_width, height=rgb_height, framerate=framerate)
    client.open()

    while True:
        try:
            data = client.get_next_packet()
            frame = data.payload
            cv2.imshow("RGB Stream", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"Error: {e}")
            break

    client.close()
    cv2.destroyAllWindows()

# Run the RGB camera stream
stream_rgb_camera()
