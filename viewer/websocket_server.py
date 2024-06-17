from flask import Flask, Response
import cv2
import hl2ss
import hl2ss_lnm

app = Flask(__name__)

# Settings
host = "192.168.2.39"
mode = hl2ss.StreamMode.MODE_1
enable_mrc = True
width = 1920
height = 1080
framerate = 30
divisor = 1
profile = hl2ss.VideoProfile.H265_MAIN
decoded_format = 'bgr24'

hl2ss_lnm.start_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, enable_mrc=enable_mrc)

client = hl2ss_lnm.rx_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO, mode=mode, width=width, height=height, framerate=framerate, divisor=divisor, profile=profile, decoded_format=decoded_format)
client.open()

def generate_frames():
    while True:
        data = client.get_next_packet()
        frame = data.payload.image

        # Encode the frame to JPEG format
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Yield the frame as a multipart HTTP response
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

client.close()
hl2ss_lnm.stop_subsystem_pv(host, hl2ss.StreamPort.PERSONAL_VIDEO)
