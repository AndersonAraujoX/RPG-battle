import os
import shutil

files_to_move = [
    "debug_combat.py", "debug_game_class.py", "debug_import.py", "debug_move.py",
    "debug_output.txt", "reproduce_crash.py", "test_dims.py", "test_log_debug.txt",
    "test_music.py", "test_output.txt", "test_output_2.txt", "test_output_3.txt",
    "test_output_verbose.txt", "test_result.txt", "game_log.txt", "fix_cerco.py",
    "converter_audio.py", "slice_sprites.py"
]

for f in files_to_move:
    if os.path.exists(f):
        target = os.path.join("tools", f)
        if os.path.exists(target):
            os.remove(target)
        shutil.move(f, target)
        print(f"Moved {f} -> {target}")
