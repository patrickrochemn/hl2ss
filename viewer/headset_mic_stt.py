import vosk
import sounddevice as sd
import queue
import json
import sys

# Set up the Vosk model
model_path = "viewer/vosk-model-small-en-us-0.15"
model = vosk.Model(model_path)

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
                # Print the recognized text on the same line
                sys.stdout.write("\rYou said: " + text)
                sys.stdout.flush()
            else:
                partial_result = rec.PartialResult()
                partial_text = json.loads(partial_result)["partial"]
                # Print the partial result on the same line
                sys.stdout.write("\rPartial: " + partial_text)
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\nProgram interrupted manually.")

    finally:
        print("\nProgram terminated.")
