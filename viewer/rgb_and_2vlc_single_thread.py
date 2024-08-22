import cv2
import hl2ss
import hl2ss_lnm

# Settings
host = "192.168.2.38"

# Stream settings for VLC cameras
vlc_ports = [hl2ss.StreamPort.RM_VLC_LEFTFRONT, hl2ss.StreamPort.RM_VLC_RIGHTFRONT]
vlc_mode = hl2ss.StreamMode.MODE_1

# Stream settings for RGB camera
rgb_mode = hl2ss.StreamMode.MODE_0
width = 1920
height = 1080
framerate = 30
profile = hl2ss.VideoProfile.H265_MAIN
decoded_format = 'bgr24'

# Global variable to control the running state
running = True

def stream_all_cameras():
    global running

    # Initialize VLC clients
    vlc_clients = []
    for port in vlc_ports:
        client = hl2ss_lnm.rx_rm_vlc(host, port, vlc_mode)
        client.open()
        vlc_clients.append(client)

    # Initialize RGB client
    hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)
    rgb_client = hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, mode=rgb_mode, width=width, height=height, framerate=framerate, profile=profile, decoded_format=decoded_format)
    rgb_client.open()

    while running:
        try:
            # Get VLC frames
            vlc_frames = []
            for i, client in enumerate(vlc_clients):
                data = client.get_next_packet()
                frame = data.payload
                # Ensure VLC frames have 3 dimensions
                if len(frame.shape) == 2:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                # Apply rotation
                if i == 0:  # Left camera
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                else:  # Right camera
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                vlc_frames.append(frame)

            # Get RGB frame
            rgb_data = rgb_client.get_next_packet()
            rgb_frame = rgb_data.payload.image

            # Display VLC and RGB frames in separate windows
            cv2.imshow('VLC Left Camera', vlc_frames[0])
            cv2.imshow('VLC Right Camera', vlc_frames[1])
            cv2.imshow('RGB Camera', rgb_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except Exception as e:
            print(f"Error in streaming: {e}")
            break

    # Cleanup
    for client in vlc_clients:
        client.close()
    rgb_client.close()
    hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)
    cv2.destroyAllWindows()

# Run the streaming function
stream_all_cameras()
