import os
import re
import sys
import uuid

base_dir = "./accepted"

def main():
    if len(sys.argv) != 2:
        print("Error - please run script as follows:")
        print("    python renum_acc.py <prefix>")
        sys.exit(1)
    prefix = sys.argv[1]
    
    # regex pattern for identifying file prefix
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)\.wav$")
    
    # create a list of tuples (number, file)
    files = []
    for f in os.listdir(base_dir):
        match = pattern.match(f)
        if match:
            number = int(match.group(1))
            files.append((number, f))       
    if not files:
        print("Error: No matching files found.")
        return
    
    # sort files by original number
    files.sort(key=lambda x: x[0])
    
    # rename files to temporary names
    temp_files = []
    for i, (_, filename) in enumerate(files):
        src = os.path.join(base_dir, filename)
        tmp_name = f"_tmp_{uuid.uuid4().hex}.wav"
        tmp = os.path.join(base_dir, tmp_name)
        os.rename(src, tmp)
        temp_files.append(tmp_name)
        print(f"{filename} -> {tmp_name}")
    # rename to final, sequential names
    for i, tmp_name in enumerate(temp_files, start=1):
        src = os.path.join(base_dir, tmp_name)
        fin_name = f"{prefix}_{i:03d}.wav"
        fin = os.path.join(base_dir, fin_name)
        os.rename(src, fin)
        print(f"{tmp_name} -> {fin_name}")
    
if __name__ == "__main__":
    main()