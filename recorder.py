"""
Record batches of samples of guitar audio, sending 
them to a folder to be reviewed individually.
"""
import sounddevice as sd
import soundfile as sf
import numpy as np
import librosa
import time
import os
import msvcrt

# === config ===
base_folder = ""                # folder used to save recorded files in
input_type = "DI"               # input device used ("DI" or "Microphone")
guitar = "IbanezJem77P"         # guitar used in recording
pickup = "Bridge"               # pickup used in recording
note_label = "0-00"             # string (0-5) and fret (0-12) of the note
sample_rate = 48000             # sample rate of recording (match with StringSense)
duration = 1.0                  # duration of each recording
num_samples = 60                # number of recordings in one batch
input_device = None             # None = default, or set the device index manually
channels = 1                    # number of channels (1 for mono, 2 for stereo)
pause_before = 1.0              # seconds to wait before a recording

# initialize folder and environment
review_folder = os.path.join(base_folder, "to_review")
os.makedirs(review_folder, exist_ok=True)

# list input devices
def list_devices():
    print(sd.query_devices())
    
# waits for the user to press enter to continue
def clear_input_buffer():
    while msvcrt.kbhit():
        msvcrt.getch()
    
# displays a countdown of the given number 
# of seconds to two/three decimal points
def countdown(total_secs):
    total_ms = total_secs * 1000
    start = time.time()
    while True:
        elapsed = (time.time() - start) * 1000
        remaining = max(0, total_ms - int(elapsed))
        print(f"Recording in: {remaining / 1000}s", end='\r')
        if remaining == 0:
            break
        time.sleep(0.01)

# checks if a sample could contain audio that is clipping
def detect_clipping(sample):
    peak = np.max(np.abs(sample))
    if peak >= 0.99:
        print(f"CLIPPING DETECTED (peak: {peak:.3f}) - consider re-recording.")
        return True
    return False

# promts the user to make a decision in case of a potential need for a retake
def prompt_retake():
    clear_input_buffer()
    res = input("Choose what to do after recording this sample:" \
          "  r - retake" \
          "  n - move on to next take" \
          "  q - quit early")
    if (res != "r" or res != "n" or res != "q"):
        print("Error: Please input one of the listed options.")
        return prompt_retake()
    return res

# record a batch of samples based on config values
def record_batch():
    # 1. print recording info
    print('=' * 65)
    print("Guitar Note Sample Recorder --- :)")
    print(f"Input Type: {input_type} | Guitar: {guitar} | Pickup: {pickup}")
    print(f"String/Fret: {note_label} | Duration: {duration}s | Samples: {num_samples}")
    print(f"Saving to: {review_folder}")
    print('=' * 65)
    
    # 2. create prefix to be used in filenames
    filename_prefix = f"{input_type}_{guitar}_{pickup}_{note_label}"

    # 3. determine file numbers (any existing files with same prefix?)
    similar_filenames = [f for f in os.listdir(review_folder) 
                         if f.startswith(filename_prefix) and f.endswith(".wav")]
    start_filename_index = len(similar_filenames) + 1

    # 4. recording loop
    i = 0
    while i <= num_samples:       
        # wait for user to press enter when ready
        clear_input_buffer()
        ipt = input(f"[{i}/{num_samples}] Press enter to start recording.")
        if ipt == "r":
            i = i - 1
            print(f"[{i}/{num_samples}] RETAKE - Press enter to start recording.")

        # create filename and filepath
        filename = f"{filename_prefix}_{(start_filename_index + i):02d}.wav"
        filepath = os.path.join(review_folder, filename)
        
        # countdown
        countdown(pause_before)
        print(f"Recording ({duration}s)... ", end='\r')
        
        # record
        sample = sd.rec(int(sample_rate * duration), samplerate=sample_rate,
                        channels=channels, dtype='float64')
        sd.wait()
        print("Recording finished! Saving to file.")
        
        # detect clipping (if so, prompt retake)
        has_clipped = detect_clipping(sample)
        if has_clipped:
            res = prompt_retake()
            if res == "r":
                i = i - 1
            if res == "n":
                pass
            if res == "q":
                break
            
        
        # trim silence
        sample_trimmed, index = librosa.effects.trim(sample, top_db=20)
        
        # normalize (after trimming)
        target_peak = 0.9
        max_peak = np.max(np.abs(sample_trimmed))
        if max_peak > 0:
            sample_trim_norm = sample_trimmed * (target_peak / max_peak)
        
        # save wav file
        sf.write(filepath, sample_trim_norm, sample_rate)
        print(f"Saved: {filename}")

    # 5. print summary after done
    print(f"Done! {i} samples saved to {base_folder}\\to_review")

# main function
if __name__ == "__main__":
    # call list_devices() to find what index your preferred input_device is
    # list_devices()
    if input_device:
        sd.default.device = input_device, None
    record_batch()

""" Notes:
    - The user will have to execute the review script 
    to actually approve each file for use.
    - Out of 60 samples, the following should be varied in playing:
        . Picking location (near neck, middle, near bridge),
        try to be centered mostly
        . Dynamics (soft, medium, hard)
        . Timing (longer vs. shorter)
        . Fret noise (finger movement)
"""
