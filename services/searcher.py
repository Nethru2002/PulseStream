import os
import re
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
        raw_input = raw_input.strip()

        yt_match = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', raw_input)
        if yt_match:
            video_id = yt_match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"

        return raw_input

    def search_tracks(self, query, limit=8):
        cleaned = self.clean_url(query)
        is_direct_url = cleaned.startswith("http://") or cleaned.startswith("https://")

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

                    v_id = entry.get("id") or ""
                    if not v_id:
                        entry_url = entry.get("url") or ""
                        id_search = re.search(r'([0-9A-Za-z_-]{11})', entry_url)
                        if id_search:
                            v_id = id_search.group(1)

                    title = entry.get("title", "Unknown Title")
                    artist = entry.get("uploader", entry.get("channel", "YouTube Artist"))
                    duration = entry.get("duration", 0) or 0

                    webpage_url = f"https://www.youtube.com/watch?v={v_id}" if v_id else (entry.get("url") or "")
                    thumbnail = entry.get("thumbnail") or (f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg" if v_id else "")

                    tracks.append({
                        "id": v_id,
                        "title": title,
                        "artist": artist,
                        "duration": float(duration),
                        "url": webpage_url,
                        "path": webpage_url,
                        "thumbnail": thumbnail,
                        "source": "STREAM"
                    })
            except Exception:
                pass
        return tracks

    def download_track(self, track_data):
        safe_name = sanitize_filename(f"{track_data['artist']} - {track_data['title']}")
        if not safe_name:
            safe_name = f"track_{track_data.get('id', 'temp')}"

        target_file = os.path.join(self.cache_dir, f"{safe_name}.mp3")
        thumb_file = os.path.join(self.thumb_dir, f"{safe_name}.jpg")

        if track_data.get("thumbnail") and not os.path.exists(thumb_file):
            try:
                res = requests.get(track_data["thumbnail"], timeout=6)
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
                    "title": track_data["title"],
                    "artist": track_data["artist"],
                    "duration": track_data.get("duration", 0),
                    "path": target_file,
                    "thumbnail": thumb_file,
                    "source": "STREAM"
                }
            else:
                try:
                    os.remove(target_file)
                except Exception:
                    pass

        for entry in os.listdir(self.cache_dir):
            if entry.startswith(safe_name) and not entry.endswith(".mp3"):
                try:
                    os.remove(os.path.join(self.cache_dir, entry))
                except Exception:
                    pass

        target_url = self.clean_url(track_data.get("url") or track_data.get("path"))

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.cache_dir, f"{safe_name}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'overwrites': True,
            'continuedl': False,
            'ffmpeg_location': self.ffmpeg_path,
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
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target_url])

        if not os.path.exists(target_file):
            for candidate in os.listdir(self.cache_dir):
                if candidate.startswith(safe_name) and candidate.endswith(".mp3"):
                    target_file = os.path.join(self.cache_dir, candidate)
                    break

        if not os.path.exists(target_file):
            raise RuntimeError(f"FFmpeg failed to assemble stream file for: {track_data['title']}")

        return {
            "title": track_data["title"],
            "artist": track_data["artist"],
            "duration": track_data.get("duration", 0),
            "path": target_file,
            "thumbnail": thumb_file,
            "source": "STREAM"
        }