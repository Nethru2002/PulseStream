import sqlite3
import os
import time
from utils.helpers import clean_track_metadata, is_corporate_channel

class DatabaseManager:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self._init_db()
        self._cleanup_invalid_tracks()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    duration REAL DEFAULT 0,
                    path TEXT UNIQUE NOT NULL,
                    thumbnail TEXT,
                    is_favorite INTEGER DEFAULT 0,
                    source TEXT DEFAULT 'LOCAL',
                    play_count INTEGER DEFAULT 0,
                    url TEXT DEFAULT '',
                    created_at REAL
                )
            """)
            try:
                cursor.execute("ALTER TABLE tracks ADD COLUMN url TEXT DEFAULT ''")
            except Exception:
                pass

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_path TEXT NOT NULL,
                    played_at REAL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at REAL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlist_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER NOT NULL,
                    track_id INTEGER NOT NULL,
                    added_at REAL,
                    UNIQUE(playlist_id, track_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    searched_at REAL
                )
            """)
            conn.commit()

    def _cleanup_invalid_tracks(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM tracks 
                WHERE LOWER(title) LIKE '%unknown title%' 
                   OR LOWER(artist) LIKE '%youtube artist%'
                   OR title = ''
            """)
            cursor.execute("SELECT id, title, artist FROM tracks")
            rows = cursor.fetchall()
            for r in rows:
                c_title, c_artist = clean_track_metadata(r["title"], r["artist"])
                if c_title != r["title"] or c_artist != r["artist"]:
                    cursor.execute("UPDATE tracks SET title = ?, artist = ? WHERE id = ?", (c_title, c_artist, r["id"]))
            cursor.execute("""
                DELETE FROM playlist_tracks 
                WHERE track_id NOT IN (SELECT id FROM tracks)
            """)
            conn.commit()

    def record_search(self, query):
        clean = str(query).strip()
        if not clean or clean.startswith("http"):
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO search_history (query, searched_at) VALUES (?, ?)", (clean, time.time()))
            conn.commit()

    def get_recent_searches(self, limit=5):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT query, MAX(searched_at) AS last_seen
                FROM search_history
                GROUP BY LOWER(query)
                ORDER BY last_seen DESC
                LIMIT ?
            """, (limit,))
            return [row["query"] for row in cursor.fetchall()]

    def get_top_artists(self, limit=5):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT artist, SUM(play_count + (is_favorite * 4)) AS score
                FROM tracks
                WHERE LOWER(artist) NOT IN ('unknown artist', 'popular artist', 'youtube artist', 'local artist', 'various artists', '')
                GROUP BY LOWER(artist)
                ORDER BY score DESC
            """)
            valid_artists = []
            for row in cursor.fetchall():
                art = row["artist"]
                if not is_corporate_channel(art):
                    valid_artists.append(art)
                    if len(valid_artists) == limit:
                        break
            return valid_artists

    def get_frequent_tracks(self, limit=12):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tracks
                WHERE LOWER(title) NOT LIKE '%unknown title%'
                ORDER BY (play_count * 2 + is_favorite * 5) DESC, created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_played_tracks(self, limit=5):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.*, MAX(h.played_at) AS last_played
                FROM history h
                JOIN tracks t ON h.track_path = t.path OR (t.url != '' AND h.track_path = t.url)
                WHERE LOWER(t.title) NOT LIKE '%unknown title%'
                GROUP BY LOWER(t.title), LOWER(t.artist)
                ORDER BY last_played DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_analytics_summary(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total_history, SUM(t.duration) AS total_sec FROM history h JOIN tracks t ON h.track_path = t.path OR (t.url != '' AND h.track_path = t.url)")
            h_stat = cursor.fetchone()
            total_plays = h_stat["total_history"] or 0
            total_seconds = h_stat["total_sec"] or 0

            cursor.execute("SELECT COUNT(*) AS fav_count FROM tracks WHERE is_favorite = 1")
            fav_count = cursor.fetchone()["fav_count"] or 0

            cursor.execute("SELECT COUNT(*) AS pl_count FROM playlists")
            pl_count = cursor.fetchone()["pl_count"] or 0

            cursor.execute("""
                SELECT * FROM tracks 
                WHERE LOWER(title) NOT LIKE '%unknown title%'
                  AND play_count > 0
                ORDER BY play_count DESC, is_favorite DESC, created_at DESC
                LIMIT 1
            """)
            top_track_row = cursor.fetchone()
            top_track = dict(top_track_row) if top_track_row else None

            cursor.execute("""
                SELECT artist, SUM(play_count) AS total_plays, SUM(is_favorite) AS fav_count, COUNT(*) AS track_count
                FROM tracks
                WHERE LOWER(artist) NOT IN ('unknown artist', 'popular artist', 'youtube artist', 'local artist', 'various artists', '')
                  AND play_count > 0
                GROUP BY LOWER(artist)
                ORDER BY total_plays DESC, fav_count DESC, track_count DESC
            """)
            all_ranked_artists = [dict(r) for r in cursor.fetchall() if not is_corporate_channel(r["artist"])]

            top_artist = all_ranked_artists[0] if all_ranked_artists else None
            top_artists_5 = all_ranked_artists[:5]

            cursor.execute("""
                SELECT * FROM tracks 
                WHERE LOWER(title) NOT LIKE '%unknown title%'
                  AND play_count > 0
                ORDER BY play_count DESC, is_favorite DESC, created_at DESC
                LIMIT 5
            """)
            top_tracks_5 = [dict(r) for r in cursor.fetchall()]

            cursor.execute("""
                SELECT t.title, t.artist, t.thumbnail, t.path, t.url, t.duration, h.played_at
                FROM history h
                JOIN tracks t ON h.track_path = t.path OR (t.url != '' AND h.track_path = t.url)
                ORDER BY h.played_at DESC
                LIMIT 20
            """)
            recent_logs = [dict(r) for r in cursor.fetchall()]

            genre = self._infer_genre_affinity(cursor)

            return {
                "total_plays": total_plays,
                "total_hours": round(total_seconds / 3600.0, 1),
                "favorites_count": fav_count,
                "playlists_count": pl_count,
                "top_genre": genre,
                "all_time_track": top_track,
                "all_time_artist": top_artist,
                "top_5_tracks": top_tracks_5,
                "top_5_artists": top_artists_5,
                "recent_logs": recent_logs
            }

    def _infer_genre_affinity(self, cursor):
        cursor.execute("SELECT LOWER(title || ' ' || artist) AS text FROM tracks")
        corpus = " ".join([r["text"] for r in cursor.fetchall()])

        cursor.execute("SELECT LOWER(query) AS q FROM search_history")
        corpus += " " + " ".join([r["q"] for r in cursor.fetchall()])

        genre_weights = {
            "R&B / Soul": ["r&b", "soul", "weeknd", "frank ocean", "sza", "joji", "brent", "daniel caesar"],
            "Pop / Hit Anthems": ["pop", "taylor", "ariana", "dua lipa", "ed sheeran", "billie", "olivia", "harry styles"],
            "Hip-Hop / Rap": ["hip hop", "rap", "drake", "kendrick", "travis", "kanye", "eminem", "cole", "post malone"],
            "Electronic / Dance": ["edm", "dance", "house", "remix", "tiesto", "calvin harris", "alan walker", "avicii", "lost stories"],
            "Rock / Alternative": ["rock", "alt", "coldplay", "arctic monkeys", "queen", "linkin", "imagine dragons", "nirvana"],
            "Sinhala / Regional Fusion": ["sonduru", "ridma", "charitha", "attalage", "danith", "sanuka", "sinhala", "coke studio", "anuv jain", "arz"]
        }

        scores = {}
        for g, keywords in genre_weights.items():
            scores[g] = sum(corpus.count(kw) for kw in keywords)

        best_genre = max(scores, key=scores.get)
        return best_genre if scores[best_genre] > 0 else "Eclectic Mix"

    def create_playlist(self, name):
        clean_name = str(name).strip()
        if not clean_name:
            return None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO playlists (name, created_at) VALUES (?, ?)", (clean_name, time.time()))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def get_playlists(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM playlists ORDER BY created_at ASC")
            return [dict(r) for r in cursor.fetchall()]

    def delete_playlist(self, playlist_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
            cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
            conn.commit()

    def add_track_to_playlist(self, playlist_id, track_data):
        raw_t = track_data.get("title", "Unknown")
        raw_a = track_data.get("artist", "Unknown")
        title, artist = clean_track_metadata(raw_t, raw_a)
        path = str(track_data.get("path") or track_data.get("url") or "")
        url = str(track_data.get("url") or "")
        dur = float(track_data.get("duration", 0) or 0)
        thumb = str(track_data.get("thumbnail") or "")
        source = str(track_data.get("source") or "STREAM")

        if "unknown title" in title.lower():
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM tracks 
                WHERE path = ? 
                   OR (url != '' AND url = ?) 
                   OR (LOWER(title) = LOWER(?) AND LOWER(artist) = LOWER(?))
                LIMIT 1
            """, (path, url, title, artist))
            row = cursor.fetchone()

            if row:
                t_id = row["id"]
            else:
                cursor.execute("""
                    INSERT INTO tracks (title, artist, duration, path, thumbnail, source, url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, artist, dur, path, thumb, source, url, time.time()))
                t_id = cursor.lastrowid

            try:
                cursor.execute("""
                    INSERT INTO playlist_tracks (playlist_id, track_id, added_at)
                    VALUES (?, ?, ?)
                """, (playlist_id, t_id, time.time()))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_track_from_playlist(self, playlist_id, track_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?", (playlist_id, track_id))
            conn.commit()

    def get_playlist_tracks(self, playlist_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.* FROM tracks t
                JOIN playlist_tracks pt ON t.id = pt.track_id
                WHERE pt.playlist_id = ?
                ORDER BY pt.added_at DESC
            """, (playlist_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_playlist_by_id(self, playlist_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_or_update_track(self, title, artist, duration, path, thumbnail="", source="LOCAL", url=""):
        c_title, c_artist = clean_track_metadata(title, artist)

        if "unknown title" in c_title.lower() or not c_title:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, is_favorite, path, url, thumbnail FROM tracks 
                WHERE path = ? 
                   OR (url != '' AND url = ?) 
                   OR (LOWER(title) = LOWER(?) AND LOWER(artist) = LOWER(?))
                LIMIT 1
            """, (path, url, c_title, c_artist))
            existing = cursor.fetchone()

            if existing:
                best_path = path if not str(path).startswith("http") else existing["path"]
                best_url = url if url else existing["url"]
                best_thumb = thumbnail if thumbnail and os.path.exists(thumbnail) else existing["thumbnail"]

                if best_path != existing["path"]:
                    cursor.execute("DELETE FROM tracks WHERE path = ? AND id != ?", (best_path, existing["id"]))

                cursor.execute("""
                    UPDATE tracks SET
                        title = ?,
                        artist = ?,
                        duration = CASE WHEN ? > 0 THEN ? ELSE duration END,
                        path = ?,
                        thumbnail = ?,
                        url = ?,
                        source = ?
                    WHERE id = ?
                """, (c_title, c_artist, duration, duration, best_path, best_thumb, best_url, source, existing["id"]))
            else:
                cursor.execute("""
                    INSERT INTO tracks (title, artist, duration, path, thumbnail, source, url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        title = excluded.title,
                        artist = excluded.artist,
                        duration = CASE WHEN excluded.duration > 0 THEN excluded.duration ELSE tracks.duration END,
                        thumbnail = CASE WHEN excluded.thumbnail != '' THEN excluded.thumbnail ELSE tracks.thumbnail END,
                        url = CASE WHEN excluded.url != '' THEN excluded.url ELSE tracks.url END
                """, (c_title, c_artist, duration, path, thumbnail, source, url, time.time()))

            conn.commit()

    def toggle_favorite_track(self, track_data):
        identifier = track_data.get("path") or track_data.get("url") or track_data.get("id")
        raw_url = track_data.get("url", "")
        raw_t = track_data.get("title", "")
        raw_a = track_data.get("artist", "")
        title, artist = clean_track_metadata(raw_t, raw_a)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, is_favorite, path FROM tracks 
                WHERE path = ? 
                   OR (url != '' AND url = ?) 
                   OR (LOWER(title) = LOWER(?) AND LOWER(artist) = LOWER(?))
                LIMIT 1
            """, (identifier, raw_url, title, artist))
            row = cursor.fetchone()

            if row:
                new_state = 0 if row["is_favorite"] == 1 else 1
                cursor.execute("UPDATE tracks SET is_favorite = ? WHERE id = ?", (new_state, row["id"]))
                conn.commit()
                return new_state == 1
            else:
                cursor.execute("""
                    INSERT INTO tracks (title, artist, duration, path, thumbnail, source, url, is_favorite, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                    ON CONFLICT(path) DO UPDATE SET is_favorite = 1
                """, (
                    title if title else "Unknown",
                    artist if artist else "Various Artists",
                    track_data.get("duration", 0),
                    identifier,
                    track_data.get("thumbnail", ""),
                    track_data.get("source", "STREAM"),
                    raw_url,
                    time.time()
                ))
                conn.commit()
                return True

    def toggle_favorite(self, path):
        if not path:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, is_favorite FROM tracks WHERE path = ?", (path,))
            row = cursor.fetchone()
            if row:
                new_state = 0 if row["is_favorite"] == 1 else 1
                cursor.execute("UPDATE tracks SET is_favorite = ? WHERE id = ?", (new_state, row["id"]))
                conn.commit()
                return new_state == 1
            return False

    def is_favorite(self, path_or_url):
        if not path_or_url:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT is_favorite FROM tracks 
                WHERE path = ? OR (url != '' AND url = ?)
            """, (path_or_url, path_or_url))
            row = cursor.fetchone()
            return bool(row["is_favorite"]) if row else False

    def record_play(self, path):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tracks SET play_count = play_count + 1 WHERE path = ?", (path,))
            cursor.execute("INSERT INTO history (track_path, played_at) VALUES (?, ?)", (path, time.time()))
            conn.commit()

    def get_favorites(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tracks 
                WHERE is_favorite = 1 
                  AND LOWER(title) NOT LIKE '%unknown title%'
                GROUP BY LOWER(title), LOWER(artist)
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_history(self, limit=50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.*, MAX(h.played_at) AS last_played
                FROM history h
                JOIN tracks t ON h.track_path = t.path OR (t.url != '' AND h.track_path = t.url)
                WHERE LOWER(t.title) NOT LIKE '%unknown title%'
                GROUP BY LOWER(t.title), LOWER(t.artist)
                ORDER BY last_played DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_saved(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tracks 
                WHERE LOWER(title) NOT LIKE '%unknown title%'
                GROUP BY LOWER(title), LOWER(artist)
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]