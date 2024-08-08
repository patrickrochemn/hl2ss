import hl2ss
import hl2ss_lnm
import pyaudio
import wave
import numpy as np
from pynput import keyboard

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.38"

# Path to the song file
song_file = "amber's embrace.wav"

# Audio encoding profile
profile = hl2ss.AudioProfile.RAW

#------------------------------------------------------------------------------

def on_press(key):
    global enable
    enable = key != keyboard.Key.esc
    return enable

# Initialize audio stream settings
audio_format = pyaudio.paInt16
channels = 2
sample_rate = 48000

# Initialize the audio client
client = hl2ss_lnm.tx(host, hl2ss.StreamPort.SPEAKER)
client.open()

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open the song file
wf = wave.open(song_file, 'rb')

# Check if the song file format matches the expected format
assert wf.getnchannels() == channels
assert wf.getframerate() == sample_rate
assert wf.getsampwidth() == p.get_sample_size(audio_format)

# Read the audio data
frames = wf.readframes(wf.getnframes())
audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

# Send the audio data to the HoloLens
enable = True
listener = keyboard.Listener(on_press=on_press)
listener.start()

while enable and len(audio_data) > 0:
    packet_size = 1024
    chunk = audio_data[:packet_size]
    client.send(chunk.tobytes())
    audio_data = audio_data[packet_size:]

# Cleanup
client.close()
listener.join()
p.terminate()
