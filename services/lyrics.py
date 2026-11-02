import requests
import re
import urllib.parse
from utils.helpers import clean_track_metadata

class LyricsService:
    def __init__(self):
        self.base_url = "https://lrclib.net/api"

    def fetch_lyrics(self, track_name, artist_name="", duration=0):
        clean_title, clean_artist = clean_track_metadata(track_name, artist_name)

        exact_res = self._query_lrclib_get(clean_title, clean_artist, duration)
        if exact_res:
            return exact_res

        search_res = self._query_lrclib_search(clean_title, clean_artist)
        if search_res:
            return search_res

        if clean_title != track_name:
            fallback_res = self._query_lrclib_search(track_name, "")
            if fallback_res:
                return fallback_res

        return {"type": "none", "text": "No synchronized lyrics found for this song."}

    def _query_lrclib_get(self, track_name, artist_name, duration):
        try:
            params = {
                "track_name": track_name,
                "artist_name": artist_name
            }
            if duration and duration > 0:
                params["duration"] = int(duration)
            resp = requests.get(f"{self.base_url}/get", params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("syncedLyrics"):
                    return {"type": "synced", "lines": self._parse_synced(data["syncedLyrics"])}
                if data.get("plainLyrics"):
                    return {"type": "plain", "text": data["plainLyrics"]}
        except Exception:
            pass
        return None

    def _query_lrclib_search(self, track_name, artist_name):
        try:
            q = f"{track_name} {artist_name}".strip()
            resp = requests.get(f"{self.base_url}/search", params={"q": q}, timeout=5)
            if resp.status_code == 200:
                items = resp.json()
                if not items or not isinstance(items, list):
                    return None

                target_tokens = set(re.findall(r'\w+', track_name.lower()))

                for item in items:
                    candidate_name = str(item.get("trackName") or "").lower()
                    candidate_artist = str(item.get("artistName") or "").lower()
                    candidate_tokens = set(re.findall(r'\w+', candidate_name))

                    overlap = target_tokens.intersection(candidate_tokens)
                    match_ratio = len(overlap) / max(len(target_tokens), 1)

                    if match_ratio >= 0.4 or (artist_name and artist_name.lower() in candidate_artist):
                        if item.get("syncedLyrics"):
                            return {"type": "synced", "lines": self._parse_synced(item["syncedLyrics"])}
                        if item.get("plainLyrics"):
                            return {"type": "plain", "text": item["plainLyrics"]}
        except Exception:
            pass
        return None

    def _parse_synced(self, synced_text):
        parsed = []
        for line in synced_text.splitlines():
            line = line.strip()
            if line.startswith("[") and "]" in line:
                time_part, text = line.split("]", 1)
                time_str = time_part[1:].strip()
                try:
                    parts = time_str.split(":")
                    if len(parts) == 2:
                        minutes = float(parts[0])
                        secs = float(parts[1])
                        timestamp = minutes * 60 + secs
                        parsed.append((timestamp, text.strip()))
                except Exception:
                    continue
        parsed.sort(key=lambda x: x[0])
        return parsed