import requests
import urllib.parse

class LyricsService:
    def __init__(self):
        self.base_url = "https://lrclib.net/api"

    def fetch_lyrics(self, track_name, artist_name="", duration=0):
        try:
            params = {
                "track_name": track_name,
                "artist_name": artist_name
            }
            if duration > 0:
                params["duration"] = int(duration)
            response = requests.get(f"{self.base_url}/get", params=params, timeout=6)
            if response.status_code == 200:
                data = response.json()
                if data.get("syncedLyrics"):
                    return {"type": "synced", "lines": self._parse_synced(data["syncedLyrics"])}
                if data.get("plainLyrics"):
                    return {"type": "plain", "text": data["plainLyrics"]}

            query = f"{track_name} {artist_name}".strip()
            search_resp = requests.get(f"{self.base_url}/search", params={"q": query}, timeout=6)
            if search_resp.status_code == 200:
                results = search_resp.json()
                if results and isinstance(results, list):
                    best = results[0]
                    if best.get("syncedLyrics"):
                        return {"type": "synced", "lines": self._parse_synced(best["syncedLyrics"])}
                    if best.get("plainLyrics"):
                        return {"type": "plain", "text": best["plainLyrics"]}
            return {"type": "none", "text": "No lyrics found."}
        except Exception:
            return {"type": "none", "text": "Lyrics temporarily unavailable."}

    def _parse_synced(self, synced_text):
        parsed = []
        for line in synced_text.splitlines():
            line = line.strip()
            if line.startswith("[") and "]" in line:
                time_part, text = line.split("]", 1)
                time_str = time_part[1:]
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