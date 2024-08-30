import hl2ss
import hl2ss_lnm
import pyaudio
import queue
import threading
import vosk
import json
import sys
import numpy as np

# Settings
host = "192.168.2.38"
profile = hl2ss.AudioProfile.RAW  # Use RAW profile

# Audio format
audio_format = pyaudio.paInt16  # Use paInt16 for RAW profile
channels = hl2ss.Parameters_MICROPHONE.CHANNELS
sample_rate = hl2ss.Parameters_MICROPHONE.SAMPLE_RATE

# Set up the Vosk model for STT
model_path = "viewer/vosk-model-small-en-us-0.15"
model = vosk.Model(model_path)

# Queues for audio data
audio_queue = queue.Queue()
stt_queue = queue.Queue()

# Buffer for accumulating audio data for STT
stt_buffer = b''

# Function to play audio data
def audio_player():
    p = pyaudio.PyAudio()
    stream = p.open(format=audio_format, channels=channels, rate=sample_rate, output=True)
    
    while True:
        audio_data = audio_queue.get()
        if audio_data is None:
            break
        stream.write(audio_data)
    
    stream.stop_stream()
    stream.close()
    p.terminate()

# Function to process STT
def stt_worker():
    global stt_buffer
    rec = vosk.KaldiRecognizer(model, sample_rate)
    print("Live STT is running...")

    while True:
        data = stt_queue.get()
        if data is None:
            break

        # Accumulate audio data in the buffer
        stt_buffer += data

        # Process STT when the buffer contains 20 packets (200ms of audio)
        if len(stt_buffer) >= sample_rate * 2 * channels * 0.2:
            if rec.AcceptWaveform(stt_buffer):
                result = rec.Result()
                text = json.loads(result)["text"]
                sys.stdout.write("\rYou said: " + text + "\n")
                sys.stdout.flush()
                stt_buffer = b''  # Clear the buffer after processing
            else:
                partial_result = rec.PartialResult()
                partial_text = json.loads(partial_result)["partial"]
                sys.stdout.write("\rPartial: " + partial_text)
                sys.stdout.flush()

# Function to capture audio from HoloLens microphone
def capture_audio():
    client = hl2ss_lnm.rx_microphone(host, hl2ss.StreamPort.MICROPHONE, profile=profile)
    client.open()
    print("Capturing audio from HoloLens microphone...")

    try:
        while True:
            data = client.get_next_packet()
            audio_bytes = data.payload.tobytes()

            # Send audio to both player and STT worker
            audio_queue.put(audio_bytes)
            stt_queue.put(audio_bytes)

    except KeyboardInterrupt:
        print("\nAudio capture interrupted manually.")
    finally:
        client.close()
        audio_queue.put(None)
        stt_queue.put(None)

# Start threads for audio capture, playback, and STT
audio_thread = threading.Thread(target=capture_audio)
player_thread = threading.Thread(target=audio_player)
stt_thread = threading.Thread(target=stt_worker)

audio_thread.start()
player_thread.start()
stt_thread.start()

# Wait for threads to finish
audio_thread.join()
player_thread.join()
stt_thread.join()
