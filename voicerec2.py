"""
Improvement on voicerec.py using streaming audio recording instead of blocked recording
"""
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from datetime import datetime

fs = 44100
recording = []

def callback(indata, frames, time, status):
    if status:
        print(status)
    recording.append(indata.copy())

with sd.InputStream(samplerate=fs, channels=2, callback=callback):
    input("Recording... Press Enter to stop.\n")

audio = np.concatenate(recording)
filename = f"recording_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav"
write(filename, fs, audio)

print(f"Saved as {filename}")