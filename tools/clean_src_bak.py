import os
import shutil

src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
scratch_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scratch"))
os.makedirs(scratch_dir, exist_ok=True)

for root, dirs, files in os.walk(src_dir):
    for f in files:
        if f.endswith(".bak") or f in ["method_body.py"]:
            file_path = os.path.join(root, f)
            dest_path = os.path.join(scratch_dir, f)
            if os.path.exists(dest_path):
                os.remove(dest_path)
            shutil.move(file_path, dest_path)
            print(f"Cleaned {file_path} -> {dest_path}")
