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

def clean_track_metadata(raw_title, raw_artist=""):
    title = str(raw_title or "").strip()
    artist = str(raw_artist or "").strip()

    if "|" in title:
        parts = [p.strip() for p in title.split("|") if p.strip()]
        if len(parts) >= 2:
            title = parts[0]
            if not artist or artist == "YouTube Artist":
                artist = parts[1]
    elif " - " in title and (not artist or artist == "YouTube Artist"):
        parts = [p.strip() for p in title.split(" - ", 1) if p.strip()]
        artist = parts[0]
        title = parts[1]

    noise_patterns = [
        r'\(Official\s*(?:Music)?\s*Video\)',
        r'\[Official\s*(?:Music)?\s*Video\]',
        r'\(Official\s*Audio\)',
        r'\[Official\s*Audio\]',
        r'\(Lyric\s*Video\)',
        r'\[Lyric\s*Video\]',
        r'\(Lyrics\)',
        r'\[Lyrics\]',
        r'\(Visualizer\)',
        r'\[Visualizer\]',
        r'\(Audio\)',
        r'\[Audio\]',
        r'\[4K\]',
        r'\(4K\)',
        r'\[HD\]',
        r'\(HD\)',
        r'Full\s*Video\s*Song',
    ]

    for pat in noise_patterns:
        title = re.sub(pat, '', title, flags=re.IGNORECASE).strip()

    title = re.sub(r'\s+', ' ', title).strip()
    return title, artist