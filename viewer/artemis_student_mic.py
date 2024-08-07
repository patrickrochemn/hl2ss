#------------------------------------------------------------------------------
# This script receives microphone audio from the HoloLens, saves it to a file
# in s16 format, and performs live speech-to-text (STT) outputting to the console.
# The main thread receives the data, decodes it, and puts the decoded audio samples
# in a queue. Audio stream configuration is fixed to 2 channels, 48000 Hz. 
# Press esc to stop.
#------------------------------------------------------------------------------

from pynput import keyboard
import hl2ss
import hl2ss_lnm
import hl2ss_utilities
import wave
import numpy as np
import queue
import threading
import speech_recognition as sr

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.38"

# Use the highest bitrate profile for the client stream
profile = hl2ss.AudioProfile.AAC_24000

# Output audio file
output_audio_file = "hololens_audio_s16.wav"

#------------------------------------------------------------------------------

enable = True
audio_frames = []
recognizer = sr.Recognizer()

# Function to convert float32 to int16
def float32_to_int16(float32_array):
    int16_array = (float32_array * 32767).astype(np.int16)
    return int16_array

def audio_recorder(pcmqueue):
    global enable
    while enable:
        pcm_data = pcmqueue.get()
        audio_frames.append(pcm_data)

def on_press(key):
    global enable
    enable = key != keyboard.Key.esc
    return enable

def live_stt():
    global enable
    while enable:
        if audio_frames:
            # Process the last audio frame for STT
            last_audio_frame = audio_frames[-1]
            audio_data = np.frombuffer(last_audio_frame, dtype=np.float32)
            audio_data = float32_to_int16(audio_data)
            audio_data = audio_data.tobytes()
            audio = sr.AudioData(audio_data, hl2ss.Parameters_MICROPHONE.SAMPLE_RATE, 2)
            try:
                text = recognizer.recognize_google(audio)
                print(f"STT: {text}")
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")

pcmqueue = queue.Queue()
thread_recorder = threading.Thread(target=audio_recorder, args=(pcmqueue,))
thread_stt = threading.Thread(target=live_stt)
listener = keyboard.Listener(on_press=on_press)
thread_recorder.start()
thread_stt.start()
listener.start()

client = hl2ss_lnm.rx_microphone(host, hl2ss.StreamPort.MICROPHONE, profile=profile)
client.open()

while enable: 
    data = client.get_next_packet()
    audio = hl2ss_utilities.microphone_planar_to_packed(data.payload)
    pcmqueue.put(audio.tobytes())

client.close()

enable = False
pcmqueue.put(b'')
thread_recorder.join()
thread_stt.join()
listener.join()

# Save audio to file in s16 format
audio_frames_combined = np.frombuffer(b''.join(audio_frames), dtype=np.float32)
audio_s16 = float32_to_int16(audio_frames_combined)
wf_s16 = wave.open(output_audio_file, 'wb')
wf_s16.setnchannels(hl2ss.Parameters_MICROPHONE.CHANNELS)
wf_s16.setsampwidth(2)  # 2 bytes for s16
wf_s16.setframerate(hl2ss.Parameters_MICROPHONE.SAMPLE_RATE)
wf_s16.writeframes(audio_s16.tobytes())
wf_s16.close()

print(f"Audio saved to {output_audio_file}")
