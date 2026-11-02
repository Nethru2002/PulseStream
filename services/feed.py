import threading
import time

class FeedEngine:
    def __init__(self, db, searcher):
        self.db = db
        self.searcher = searcher
        self.cached_shelves = []
        self.last_generated_at = 0
        self.is_busy = False

    def get_instant_feed(self):
        shelves = []
        jump_back = self.db.get_frequent_tracks(limit=8)
        if jump_back:
            shelves.append({
                "title": "Jump Back In",
                "subtitle": "Your most played tracks & recent favorites",
                "tracks": jump_back
            })
        if self.cached_shelves:
            for s in self.cached_shelves:
                if s["title"] != "Jump Back In":
                    shelves.append(s)
        return shelves

    def generate_feed_async(self, on_ready_callback, force=False):
        now = time.time()
        if not force and (now - self.last_generated_at) < 180 and self.cached_shelves:
            on_ready_callback(self.get_instant_feed())
            return

        if self.is_busy:
            return

        self.is_busy = True

        def worker():
            try:
                new_shelves = []
                frequent = self.db.get_frequent_tracks(limit=8)
                if frequent:
                    new_shelves.append({
                        "title": "Jump Back In",
                        "subtitle": "Your most played tracks & recent favorites",
                        "tracks": frequent
                    })

                top_artists = self.db.get_top_artists(limit=2)
                for art in top_artists:
                    recs = self.searcher.search_tracks(f"{art} top songs", limit=6)
                    clean_recs = [t for t in recs if t.get("title") and "unknown title" not in t["title"].lower()]
                    if clean_recs:
                        new_shelves.append({
                            "title": f"Because You Listen to {art}",
                            "subtitle": f"Similar releases & curated hits by {art}",
                            "tracks": clean_recs
                        })

                searches = self.db.get_recent_searches(limit=2)
                for q in searches:
                    s_recs = self.searcher.search_tracks(f"{q} playlist audio", limit=6)
                    clean_s = [t for t in s_recs if t.get("title") and "unknown title" not in t["title"].lower()]
                    if clean_s:
                        new_shelves.append({
                            "title": f"Inspired by '{q}'",
                            "subtitle": "Fresh tracks matching your search intent",
                            "tracks": clean_s
                        })

                discoveries = self.searcher.search_tracks("Billboard top trending songs 2026", limit=8)
                clean_disc = [t for t in discoveries if t.get("title") and "unknown title" not in t["title"].lower()]
                if clean_disc:
                    new_shelves.append({
                        "title": "Global Discoveries & Fresh Finds",
                        "subtitle": "New audio releases curated across genres",
                        "tracks": clean_disc
                    })

                self.cached_shelves = new_shelves
                self.last_generated_at = time.time()
                on_ready_callback(self.cached_shelves)
            except Exception:
                pass
            finally:
                self.is_busy = False

        threading.Thread(target=worker, daemon=True).start()