"""
Simple audio recording script that runs within the command line.
Uses blocked audio recording.
"""
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from datetime import datetime
import threading

# sample rating (samples per second)
fs = 44100
# store recording as an array of ints/floats, recording boolean flag
recording, is_recording = [], True

# records audio in chunks of 0.5 seconds
def record():
    global recording
    while is_recording:
        chunk = sd.rec(int(0.5 * fs), samplerate=fs, channels=2)
        sd.wait()
        recording.append(chunk)
        
# separate thread so that main function does not freeze while recording
#start function keeps going until 'Enter' is pressed
threading.Thread(target=record).start()
input("Recording... Press Enter to stop.\n")
is_recording = False

# save file 
audio = np.concatenate(recording)
filename = f"recording_{datetime.now().strftime('%Y-%m-%d-_%H-%M-%S')}.wav"
write(filename, fs, audio)
print(f"Saved as {filename}")