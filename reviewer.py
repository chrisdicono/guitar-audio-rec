"""
Play back samples from review folder one-by-one.
"""
import sounddevice as sd
import soundfile as sf
import shutil
import time
import os

# config
base_folder = ""

# folder setup
review_folder = os.path.join(base_folder, "to_review")
accept_folder = os.path.join(base_folder, "accepted")
os.makedirs(review_folder, exist_ok=True)
os.makedirs(accept_folder, exist_ok=True)

# play the given audio file
def play_file(filepath):
    data, sr = sf.read(filepath, dtype="float32")
    sd.stop()
    with sd.OutputStream(samplerate=sr, channels=1) as s:
        s.write(data)

# reviews each sample in the "to_review" folder based on user input
def review_samples():
    # 1. retreive a list of all audio files in "to_review" folder
    rev_files = sorted([f for f in os.listdir(review_folder) if f.endswith(".wav")])
    acc_files = sorted([f for f in os.listdir(accept_folder) if f.endswith(".wav")])
    if not rev_files:
        print("No files exist to be reviewed! Please record some samples first.")
        return
    
    # 2. list commands
    print('=' * 65)
    print("Guitar Note Sample Reviewer --- :)")
    print(f"{len(rev_files)} in folder {review_folder}")
    print(f"{len(acc_files)} in folder {accept_folder}")
    print('=' * 65)
    print(f"  Controls:")
    print(f"    k - keep (move to approved)")
    print(f"    d - delete")
    print(f"    r - replay")
    print(f"    s - skip (leave in review for later)")
    print(f"    q - quit review")
    print('=' * 65)

    kept = 0
    deleted = 0
    skipped = 0

    # 3. for each file, respond to user decisions
    for i, filename in enumerate(rev_files, 1):
        filepath = os.path.join(review_folder, filename)

        print(f"[{i}/{len(rev_files)}] {filename}")
        play_file(filepath)

        while True:
            choice = input("  (k)eep / (d)elete / (r)eplay / (s)kip / (q)uit: ").strip().lower()

            if choice == "k":
                dest = os.path.join(accept_folder, filename)
                # case of duplicate file names
                if os.path.exists(dest):
                    base, ext = os.path.splitext(filename)
                    n = 1
                    while os.path.exists(dest):
                        dest = os.path.join(accept_folder, f"{base}_dup{n}{ext}")
                        n += 1
                shutil.move(filepath, dest)
                print("  File moved to approved folder.")
                kept += 1
                break
            elif choice == "d":
                confirm = input("  Confirm delete? (y/n): ").strip().lower()
                if confirm == "y":
                    os.remove(filepath)
                    print(f"  Deleted file {i}.")
                    deleted += 1
                    break
                else:
                    print("  Delete cancelled.")
                    continue
            elif choice == "r":
                play_file(filepath)
                continue
            elif choice == "s":
                print(f"  Skipped file {i}.")
                skipped += 1
                break
            elif choice == "q":
                print("Quitting sample review early.")
                return
            else:
                print("  Invalid input. Use k/d/r/s/q.")

    # 4. print resulting stats
    print(f"\nReview complete!")
    print(f"  Kept: {kept} | Deleted: {deleted} | Skipped: {skipped}")
    remaining = len([f for f in os.listdir(review_folder) if f.endswith(".wav")])
    print(f"  Still in review: {remaining}")

if __name__ == "__main__":
    review_samples()
