from pynput import keyboard
import hl2ss
import hl2ss_lnm
import hl2ss_utilities
import pyaudio
import queue
import threading
import wave
import speech_recognition as sr
import numpy as np

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.38"

# Audio encoding profile
profile = hl2ss.AudioProfile.AAC_24000

# Output file names
wav_output_file = "hololens_audio_s16.wav"
stt_output_file = "stt_output.txt"

#------------------------------------------------------------------------------


# RAW format is s16 packed, AAC decoded format is f32 planar
audio_format = pyaudio.paInt16 if (profile == hl2ss.AudioProfile.RAW) else pyaudio.paFloat32
enable = True

# Initialize recognizer
recognizer = sr.Recognizer()

def pcmworker(pcmqueue, wav_output):
    global enable
    global audio_format
    p = pyaudio.PyAudio()
    stream = p.open(format=audio_format, channels=hl2ss.Parameters_MICROPHONE.CHANNELS, rate=hl2ss.Parameters_MICROPHONE.SAMPLE_RATE, output=False)
    stream.start_stream()

    frames = []

    while enable:
        frame = pcmqueue.get()
        frames.append(frame)
        
        # Save the audio data to WAV file
        wav_output.writeframes(frame)

    stream.stop_stream()
    stream.close()
    wav_output.close()

def live_stt(pcmqueue):
    global enable
    global recognizer

    while enable:
        if not pcmqueue.empty():
            frame = pcmqueue.get()
            audio_data = np.frombuffer(frame, dtype=np.int16)
            audio_segment = sr.AudioData(audio_data.tobytes(), hl2ss.Parameters_MICROPHONE.SAMPLE_RATE, 2)

            try:
                text = recognizer.recognize_google(audio_segment)
                print(f"STT: {text}")

                # Append the recognized text to the output file
                with open(stt_output_file, 'a') as f:
                    f.write(text + '\n')

            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")

def on_press(key):
    global enable
    enable = key != keyboard.Key.esc
    return enable

pcmqueue = queue.Queue()
wav_output = wave.open(wav_output_file, 'wb')
wav_output.setnchannels(hl2ss.Parameters_MICROPHONE.CHANNELS)
wav_output.setsampwidth(pyaudio.PyAudio().get_sample_size(audio_format))
wav_output.setframerate(hl2ss.Parameters_MICROPHONE.SAMPLE_RATE)

thread_pcmworker = threading.Thread(target=pcmworker, args=(pcmqueue, wav_output))
thread_stt = threading.Thread(target=live_stt, args=(pcmqueue,))
listener = keyboard.Listener(on_press=on_press)

thread_pcmworker.start()
thread_stt.start()
listener.start()

client = hl2ss_lnm.rx_microphone(host, hl2ss.StreamPort.MICROPHONE, profile=profile)
client.open()

while enable:
    data = client.get_next_packet()
    audio = hl2ss_utilities.microphone_planar_to_packed(data.payload) if profile != hl2ss.AudioProfile.RAW else data.payload
    pcmqueue.put(audio.tobytes())

client.close()

enable = False
pcmqueue.put(b'')
thread_pcmworker.join()
thread_stt.join()
listener.join()
