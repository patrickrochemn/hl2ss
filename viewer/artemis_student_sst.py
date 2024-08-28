import hl2ss
import hl2ss_lnm
import hl2ss_utilities
import pyaudio
import queue
import threading
import speech_recognition as sr
import numpy as np

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.38"

# Audio encoding profile
profile = hl2ss.AudioProfile.AAC_24000

#------------------------------------------------------------------------------

# AAC decoded format is f32 planar
audio_format = pyaudio.paFloat32

# Audio queue for processing
pcmqueue = queue.Queue()

# Flag to control the script
enable = True

def pcmworker(pcmqueue):
    global enable
    p = pyaudio.PyAudio()
    stream = p.open(format=audio_format, channels=hl2ss.Parameters_MICROPHONE.CHANNELS, rate=hl2ss.Parameters_MICROPHONE.SAMPLE_RATE, output=True)
    stream.start_stream()
    while enable:
        data = pcmqueue.get()
        stream.write(data)
    stream.stop_stream()
    stream.close()
    p.terminate()

def stt_worker():
    global enable
    recognizer = sr.Recognizer()

    while enable:
        if not pcmqueue.empty():
            audio_data = pcmqueue.get()
            # Convert float32 to int16 for STT processing
            audio_data = np.frombuffer(audio_data, dtype=np.float32)
            audio_data = (audio_data * 32767).astype(np.int16)  # Convert float32 to int16
            # Create AudioData for STT
            audio = sr.AudioData(audio_data.tobytes(), hl2ss.Parameters_MICROPHONE.SAMPLE_RATE, 2)
            try:
                # Recognize the speech using Google Web Speech API
                text = recognizer.recognize_google(audio)
                print(f"STT Output: {text}")
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand the audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")

# Start threads
pcm_thread = threading.Thread(target=pcmworker, args=(pcmqueue,))
stt_thread = threading.Thread(target=stt_worker)
pcm_thread.start()
stt_thread.start()

# Initialize the audio client
client = hl2ss_lnm.rx_microphone(host, hl2ss.StreamPort.MICROPHONE, profile=profile)
client.open()

# Main loop to receive audio data
while enable:
    data = client.get_next_packet()
    audio = hl2ss_utilities.microphone_planar_to_packed(data.payload)  # Convert planar to packed
    pcmqueue.put(audio.tobytes())

client.close()

enable = False
pcmqueue.put(b'')
pcm_thread.join()
stt_thread.join()
