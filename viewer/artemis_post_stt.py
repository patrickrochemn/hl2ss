import speech_recognition as sr
from pydub import AudioSegment
import os

# Path to the saved audio file
audio_file_path = "hololens_audio_s16.wav"

# Convert audio file to a format that might be better recognized
audio = AudioSegment.from_wav(audio_file_path)
audio.export("converted_audio.wav", format="wav")

# Initialize recognizer
recognizer = sr.Recognizer()

# Read the converted audio file
with sr.AudioFile("converted_audio.wav") as source:
    audio_data = recognizer.record(source)

# Perform speech recognition
try:
    text = recognizer.recognize_google(audio_data)
    print(f"STT: {text}")
    
    # Save the text to a file
    with open("stt_output.txt", 'w') as f:
        f.write(text)
    
    print(f"STT results saved to stt_output.txt")
except sr.UnknownValueError:
    print("Google Speech Recognition could not understand audio")
except sr.RequestError as e:
    print(f"Could not request results from Google Speech Recognition service; {e}")

# Clean up
os.remove("converted_audio.wav")
