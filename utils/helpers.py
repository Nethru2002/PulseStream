import os
import re

def format_time(seconds):
    try:
        val = int(float(seconds))
        minutes = val // 60
        secs = val % 60
        return f"{minutes:02d}:{secs:02d}"
    except Exception:
        return "00:00"

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()