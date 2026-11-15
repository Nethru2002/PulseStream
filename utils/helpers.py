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

def is_corporate_channel(name):
    if not name:
        return True
    n = str(name).strip().lower()
    blocked = [
        "records", "music", "vevo", "entertainment", "series", "studio",
        "films", "media", "official", "topic", "company", "production",
        "broadcast", "network", "label", "t-series", "audio", "channel",
        "corporation", "sound", "recordings", "distribution"
    ]
    for b in blocked:
        if b in n:
            return True
    return False

def clean_track_metadata(raw_title, raw_artist=""):
    title = str(raw_title or "").strip()
    artist = str(raw_artist or "").strip()

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
        r'\[from\s*[^\]]+\]',
        r'\(from\s*[^\)]+\)'
    ]

    for pat in noise_patterns:
        title = re.sub(pat, '', title, flags=re.IGNORECASE).strip()

    if " - " in title:
        parts = [p.strip() for p in title.split(" - ", 1) if p.strip()]
        if len(parts) == 2:
            extracted_artist, song_name = parts[0], parts[1]
            if is_corporate_channel(artist) or not artist or artist.lower() in ["youtube artist", "unknown artist", "popular artist"]:
                artist = extracted_artist
            title = song_name
    elif "|" in title:
        parts = [p.strip() for p in title.split("|") if p.strip()]
        if len(parts) >= 2:
            title = parts[0]
            if is_corporate_channel(artist) or not artist or artist.lower() in ["youtube artist", "unknown artist", "popular artist"]:
                candidate = parts[-1]
                for p in parts[1:]:
                    if not is_corporate_channel(p) and not re.search(r'video|audio|lyric|hd|4k', p, re.I):
                        candidate = p
                        break
                artist = candidate

    if artist and title.lower().startswith(f"{artist.lower()} -"):
        title = title[len(artist) + 2:].strip()
    elif artist and title.lower().startswith(f"{artist.lower()} –"):
        title = title[len(artist) + 2:].strip()

    if is_corporate_channel(artist):
        m_by = re.search(r'by\s+([A-Za-z0-9\s,&]+)', title, re.I)
        if m_by:
            artist = m_by.group(1).strip()
        else:
            m_feat = re.search(r'(?:ft\.?|feat\.?)\s+([A-Za-z0-9\s,&]+)', title, re.I)
            if m_feat:
                artist = m_feat.group(1).strip()

    title = re.sub(r'\s+', ' ', title).strip()
    artist = re.sub(r'\s+', ' ', artist).strip()

    if not title:
        title = str(raw_title or "Unknown Title").strip()
    if not artist or is_corporate_channel(artist):
        artist = str(raw_artist or "Various Artists").strip()

    return title, artist