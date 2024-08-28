import sounddevice as sd
import queue
import vosk
import json
import sys

# Set up the Vosk model
model = vosk.Model("vosk-model-small-en-us-0.15")

# Queue to hold the audio data
q = queue.Queue()

# Function to capture audio data
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# Set up the microphone stream
with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                       channels=1, callback=callback):
    rec = vosk.KaldiRecognizer(model, 16000)
    print("Listening continuously... Press 'Ctrl+C' to exit.")
    
    try:
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                text = json.loads(result)["text"]
                print("You said:", text)
            else:
                partial_result = rec.PartialResult()
                partial_text = json.loads(partial_result)["partial"]
                print("Partial:", partial_text)

    except KeyboardInterrupt:
        print("Program interrupted manually.")
    finally:
        print("Program terminated.")