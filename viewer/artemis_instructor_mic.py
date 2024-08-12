import http.server
import socketserver
import wave
import os

# Settings --------------------------------------------------------------------

# Port number for the HTTP server
PORT = 8080

# Path to the song file
song_file = "amber's embrace.wav"

#------------------------------------------------------------------------------

class AudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve the audio file when requested
        if self.path == '/':
            print(f"Received request for {song_file}")
            if os.path.exists(song_file):
                print(f"Serving {song_file}")
                self.send_response(200)
                self.send_header("Content-type", "audio/wav")
                self.end_headers()
                with open(song_file, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                print(f"File not found: {song_file}")
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Invalid path")

# Set up the server
with socketserver.TCPServer(("", PORT), AudioRequestHandler) as httpd:
    print(f"Serving audio on port {PORT}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")
        httpd.shutdown()
