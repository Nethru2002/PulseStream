import os
import re
import time
import urllib.parse
import requests
import yt_dlp
from utils.helpers import ensure_dir, sanitize_filename

class StreamSearcher:
    def __init__(self):
        self.cache_dir = os.path.abspath("cache")
        self.thumb_dir = os.path.join(self.cache_dir, "thumbs")
        ensure_dir(self.cache_dir)
        ensure_dir(self.thumb_dir)
        self.ffmpeg_path = os.path.abspath(".")

    def clean_url(self, raw_input):
        if not raw_input:
            return ""
        raw_input = str(raw_input).strip()

        if "youtube.com" in raw_input or "youtu.be" in raw_input:
            yt_match = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', raw_input)
            if yt_match:
                video_id = yt_match.group(1)
                return f"https://www.youtube.com/watch?v={video_id}"

        return raw_input

    def get_cached_path(self, track_data):
        if not track_data or not isinstance(track_data, dict):
            return None

        p = str(track_data.get("path") or "").strip()
        if p and not p.startswith("http"):
            if os.path.isabs(p) and os.path.exists(p) and os.path.getsize(p) > 50000:
                return os.path.abspath(p)
            rel_p = os.path.join(self.cache_dir, os.path.basename(p))
            if os.path.exists(rel_p) and os.path.getsize(rel_p) > 50000:
                return os.path.abspath(rel_p)

        raw_url = str(track_data.get("url") or "").strip()
        v_id = ""

        m = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', raw_url)
        if m:
            v_id = m.group(1)
        elif p:
            m = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', p)
            if m:
                v_id = m.group(1)
            else:
                base = os.path.splitext(os.path.basename(p))[0]
                if len(base) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', base) and base != "PulseStream":
                    v_id = base

        if not v_id:
            tid = str(track_data.get("id") or "")
            if len(tid) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', tid) and tid != "PulseStream":
                v_id = tid

        if v_id:
            id_path = os.path.join(self.cache_dir, f"{v_id}.mp3")
            if os.path.exists(id_path) and os.path.getsize(id_path) > 50000:
                return os.path.abspath(id_path)

        title = sanitize_filename(str(track_data.get("title") or "")).strip().lower()
        artist = sanitize_filename(str(track_data.get("artist") or "")).strip().lower()

        try:
            for entry in os.listdir(self.cache_dir):
                if not entry.lower().endswith(".mp3"):
                    continue
                full_path = os.path.join(self.cache_dir, entry)
                if os.path.getsize(full_path) < 50000:
                    continue

                if v_id and v_id in entry:
                    return os.path.abspath(full_path)

                clean_entry = entry.lower()
                if title and len(title) > 3 and title in clean_entry:
                    return os.path.abspath(full_path)
                if artist and len(artist) > 3 and artist in clean_entry and title and title[:8] in clean_entry:
                    return os.path.abspath(full_path)
        except Exception:
            pass

        return None

    def search_tracks(self, query, limit=8):
        cleaned = self.clean_url(query)
        is_direct_url = str(cleaned).startswith("http://") or str(cleaned).startswith("https://")

        ydl_opts = {
            'format': 'bestaudio/best',
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

        if not is_direct_url:
            ydl_opts['default_search'] = f'ytsearch{limit}'
            search_target = cleaned
        else:
            search_target = cleaned

        tracks = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                res = ydl.extract_info(search_target, download=False)
                if not res:
                    return tracks

                if 'entries' in res and res['entries']:
                    raw_entries = res['entries']
                else:
                    raw_entries = [res]

                for entry in raw_entries:
                    if not entry:
                        continue

                    v_id = str(entry.get("id") or "")
                    if not v_id:
                        entry_url = str(entry.get("url") or "")
                        id_search = re.search(r'([0-9A-Za-z_-]{11})', entry_url)
                        if id_search:
                            v_id = id_search.group(1)

                    title = entry.get("title", "Unknown Title")
                    artist = entry.get("uploader", entry.get("channel", "YouTube Artist"))
                    duration = entry.get("duration", 0) or 0

                    webpage_url = f"https://www.youtube.com/watch?v={v_id}" if v_id else str(entry.get("url") or "")
                    thumbnail = entry.get("thumbnail") or (f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg" if v_id else "")

                    probe_cached = self.get_cached_path({
                        "id": v_id,
                        "url": webpage_url,
                        "title": title,
                        "artist": artist
                    })

                    tracks.append({
                        "id": v_id,
                        "title": title,
                        "artist": artist,
                        "duration": float(duration),
                        "url": webpage_url,
                        "path": probe_cached if probe_cached else webpage_url,
                        "thumbnail": thumbnail,
                        "source": "STREAM"
                    })
            except Exception:
                pass
        return tracks

    def download_track(self, track_data, on_progress=None):
        cached_hit = self.get_cached_path(track_data)
        if cached_hit:
            return {
                "title": track_data.get("title", "Unknown Title"),
                "artist": track_data.get("artist", "Unknown Artist"),
                "duration": track_data.get("duration", 0),
                "path": cached_hit,
                "url": track_data.get("url", ""),
                "thumbnail": track_data.get("thumbnail", ""),
                "source": "STREAM"
            }

        raw_url = str(track_data.get("url") or "").strip()
        path_str = str(track_data.get("path") or "").strip()

        target_url = ""
        v_id = ""

        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            target_url = self.clean_url(raw_url)
            yt_match = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', target_url)
            if yt_match:
                v_id = yt_match.group(1)
        elif path_str.startswith("http://") or path_str.startswith("https://"):
            target_url = self.clean_url(path_str)
            yt_match = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', target_url)
            if yt_match:
                v_id = yt_match.group(1)

        if not target_url:
            filename = os.path.splitext(os.path.basename(path_str))[0]
            if len(filename) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', filename) and filename != "PulseStream":
                v_id = filename
                target_url = f"https://www.youtube.com/watch?v={v_id}"
            else:
                title = track_data.get("title", "")
                artist = track_data.get("artist", "")
                target_url = f"ytsearch1:{artist} {title}".strip()
                v_id = sanitize_filename(f"{artist}_{title}")

        if not v_id or v_id == "PulseStream":
            v_id = f"stream_{int(time.time())}"

        v_id = str(v_id)
        target_file = os.path.join(self.cache_dir, f"{v_id}.mp3")
        thumb_file = os.path.join(self.thumb_dir, f"{v_id}.jpg")

        if track_data.get("thumbnail") and not os.path.exists(thumb_file):
            try:
                res = requests.get(track_data["thumbnail"], timeout=4)
                if res.status_code == 200:
                    with open(thumb_file, "wb") as f:
                        f.write(res.content)
            except Exception:
                thumb_file = ""
        elif not os.path.exists(thumb_file):
            thumb_file = ""

        if os.path.exists(target_file):
            if os.path.getsize(target_file) > 50000:
                return {
                    "title": track_data.get("title", "Unknown Title"),
                    "artist": track_data.get("artist", "Unknown Artist"),
                    "duration": track_data.get("duration", 0),
                    "path": target_file,
                    "url": target_url if str(target_url).startswith("http") else f"https://www.youtube.com/watch?v={v_id}",
                    "thumbnail": thumb_file,
                    "source": "STREAM"
                }
            else:
                try:
                    os.remove(target_file)
                except Exception:
                    pass

        for entry in os.listdir(self.cache_dir):
            if entry.startswith(v_id) and not entry.endswith(".mp3"):
                try:
                    os.remove(os.path.join(self.cache_dir, entry))
                except Exception:
                    pass

        def ydl_hook(d):
            if not on_progress:
                return
            status = d.get('status')
            if status == 'downloading':
                percent = d.get('_percent_str', '').strip()
                clean_p = re.sub(r'\x1b\[[0-9;]*m', '', percent)
                if clean_p:
                    on_progress(f"Buffering: {clean_p}")
            elif status == 'finished':
                on_progress("Finalizing audio...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.cache_dir, f"{v_id}.%(ext)s"),
            'nopart': True,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'overwrites': True,
            'continuedl': False,
            'ffmpeg_location': self.ffmpeg_path,
            'progress_hooks': [ydl_hook],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target_url])

        if not os.path.exists(target_file):
            for candidate in os.listdir(self.cache_dir):
                if candidate.startswith(v_id) and candidate.endswith(".mp3"):
                    target_file = os.path.join(self.cache_dir, candidate)
                    break

        if not os.path.exists(target_file):
            raise RuntimeError(f"FFmpeg failed to assemble stream file for: {track_data.get('title', 'Unknown')}")

        return {
            "title": track_data.get("title", "Unknown Title"),
            "artist": track_data.get("artist", "Unknown Artist"),
            "duration": track_data.get("duration", 0),
            "path": target_file,
            "url": target_url if str(target_url).startswith("http") else f"https://www.youtube.com/watch?v={v_id}",
            "thumbnail": thumb_file,
            "source": "STREAM"
        }