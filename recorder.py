"""
Record batches of samples of guitar audio, sending 
them to a folder to be reviewed individually.
"""
import sounddevice as sd
import soundfile as sf
import numpy as np
import re
import librosa
import time
import os
import msvcrt

# === config ===
base_folder = ""                # folder used to save recorded files in
input_type = "DI"               # input device used ("DI" or "Microphone")
guitar = "FenderStrat"          # guitar used in recording
pickup = "Bridge"               # pickup used in recording
note_label = "0-03"             # string (0-5) and fret (0-12) of the note
sample_rate = 48000             # sample rate of recording (match with StringSense)
duration = 1.0                  # duration of each recording
num_samples = 60                # number of recordings in one batch
input_device = 2                # None = default, or set the device index manually
channels = 1                    # number of channels (1 for mono, 2 for stereo)
pause_before = 1.0              # seconds to wait before a recording
intermission = 1.0              # seconds between each recording, if desired to be automatic
paused = False
quit_flag = False
retake_flag = False

# initialize folder and environment
review_folder = os.path.join(base_folder, "to_review")
accept_folder = os.path.join(base_folder, "accepted")
os.makedirs(review_folder, exist_ok=True)
os.makedirs(accept_folder, exist_ok=True)

# list input devices
def list_devices():
    print(sd.query_devices())
    
# waits for the user to press enter to continue
def clear_input_buffer():
    while msvcrt.kbhit():
        msvcrt.getch()
        
# returns arrays of files with the given prefix in the accepted
# folder and the to_review folder
def get_acc_rev(prefix):
    acc = [f for f in os.listdir(accept_folder) if 
           f.startswith(prefix) and f.endswith(".wav")]
    rev = [f for f in os.listdir(review_folder) if 
           f.startswith(prefix) and f.endswith(".wav")]
    return [acc, rev]
    
    
# displays a countdown of the given number 
# of seconds to two/three decimal points
def countdown(total_secs):
    global paused, quit_flag, retake_flag
    remaining = total_secs
    step = 0.01
    while remaining > 0:
        handle_input()
        if quit_flag: return "q"
        if retake_flag: return "r"
        if paused:
            time.sleep(0.05)
            continue
        time.sleep(step)
        remaining -= step
        print(f"  Recording in: {remaining:.2f}s", end='\r')
    return "ok"

# checks if a sample could contain audio that is clipping
def detect_clipping(sample):
    peak = np.max(np.abs(sample))
    if peak >= 0.99:
        print(f"  CLIPPING DETECTED (peak: {peak:.3f}) - consider re-recording.")
        return True
    return False

# promts the user to make a decision in case of a potential need for a retake
def prompt_retake():
    clear_input_buffer()
    while True:
        res = input("  Choose what to do after recording this sample:\n" \
            "    r - retake\n" \
            "    n - move on to next take\n" \
            "    q - quit early\n").strip().lower()
        if res in {"r", "n", "q"}:
            return res
        print("  Error: Please input one of the listed options.")
        
# provides a list of available file numbers to record to given a prefix for a filename
def get_available_indices(files, prefix, count):
    pattern = re.compile(rf"{re.escape(prefix)}_(\d+)\.wav")
    
    # fill a set of all used file numbers
    used = set()
    for f in files:
        match = pattern.match(f)
        if match:
            used.add(int(match.group(1)))
    
    # fill an array with the first _count_ free file numbers
    res = []
    i = 1
    while len(res) < count:
        if i not in used:
            res.append(i)
        i += 1

    return res

# handles logic to pause and resume automated recording (intermission > 0)
def handle_input():
    global paused, quit_flag, retake_flag
    if msvcrt.kbhit():
        key = msvcrt.getch()
        if key == b' ':
            paused = not paused
            print("--- PAUSED --- (Enter - resume, q - quit)"
                  if paused else "--- RESUMED --- ")
        elif key == b'q':
            print("--- QUITTING ---")
            quit_flag = True
            return
        elif key == b'r':
            retake_flag = True
            print("--- RETAKE REQUESTED --- ")

# record a batch of samples based on config values
def record_batch():
    # 1. create prefix to be used in filenames
    filename_prefix = f"{input_type}_{guitar}_{pickup}_{note_label}"
    
    # 2. print recording info
    identical_acc, identical_rev = get_acc_rev(filename_prefix)
    acc_len = len(identical_acc)
    rev_len = len(identical_rev)
    print('=' * 65)
    print("Guitar Note Sample Recorder --- :)")
    print(f"Input Type: {input_type} | Guitar: {guitar} | Pickup: {pickup}")
    print(f"String/Fret: {note_label} | Duration: {duration}s | Samples: {num_samples}")
    print(f"Identical prefixes --- Accepted: {acc_len} | Review Needed: {rev_len}")
    print(f"Saving to: {review_folder}")
    print('=' * 65)

    # 3. determine file numbers (any existing files with same prefix?)
    fns = identical_acc + identical_rev
    indices = get_available_indices(fns, filename_prefix, num_samples)

    # 4. recording loop
    num_saved = 0
    i = 1
    min_retake = 2
    while i <= num_samples:
        # create filename and filepath
        filename = f"{filename_prefix}_{indices[i - 1]:03d}.wav"
        filepath = os.path.join(review_folder, filename)
        
        # prepare for recording and handle pause logic
        print(f"[{i}/{num_samples}] Press space to pause recording cycle. ")
        cd_res = countdown(intermission + pause_before)
        if cd_res != "ok":
            if cd_res == "q": break
            if cd_res == "r":
                global retake_flag
                retake_flag = False
                if i >= min_retake:
                    print(f"RETAKING sample {i - 1}/{num_samples}.")
                    num_saved -= 1
                    i -= 1
                continue
                    
                
        
        # record
        print(f"  Recording ({duration}s)... ", end='\r')
        sample = sd.rec(int(sample_rate * duration), samplerate=sample_rate,
                        channels=channels, dtype='float32')
        sd.wait()
        print("  Recording finished!")
        
        # detect clipping (if so, prompt retake)
        has_clipped = detect_clipping(sample)
        if has_clipped:
            res = prompt_retake().strip().lower()
            if res == "r" and i >= min_retake:
                continue
            if res == "n":
                pass
            if res == "q":
                break
            
        
        # trim silence (TODO: librosa is nice but could be more lightweight)
        sample = sample.flatten()
        sample_trimmed, index = librosa.effects.trim(sample, top_db=10)
        if len(sample_trimmed) == 0:
            print("  Trimmed audio is empty. Need to retake.")
            continue
        print("  Trimmed silence!")
        
        # normalize (after trimming)
        target_peak = 0.9
        max_peak = np.max(np.abs(sample_trimmed))
        if max_peak > 0:
            sample_trim_norm = sample_trimmed * (target_peak / max_peak)
        else:
            sample_trim_norm = sample_trimmed
        print("  Normalized!")
        
        # save wav file
        sf.write(filepath, sample_trim_norm, sample_rate)
        num_saved += 1
        print(f"  Saved: {filename}")
        i += 1

    # 5. print summary after done
    print(f"Done! {num_saved} samples saved to {base_folder}\\to_review")

# main function
if __name__ == "__main__":
    # uncomment below to find what index your preferred input_device is
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
