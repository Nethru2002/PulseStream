import sqlite3
import os
import time

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
                WHERE LOWER(artist) NOT IN ('unknown artist', 'popular artist', 'youtube artist', 'local artist', '')
                GROUP BY LOWER(artist)
                ORDER BY score DESC
                LIMIT ?
            """, (limit,))
            return [row["artist"] for row in cursor.fetchall()]

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
        title = str(track_data.get("title", "Unknown")).strip()
        artist = str(track_data.get("artist", "Unknown")).strip()
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
        clean_title = str(title).strip()
        clean_artist = str(artist).strip()

        if "unknown title" in clean_title.lower() or not clean_title:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, is_favorite, path, url, thumbnail FROM tracks 
                WHERE path = ? 
                   OR (url != '' AND url = ?) 
                   OR (LOWER(title) = LOWER(?) AND LOWER(artist) = LOWER(?))
                LIMIT 1
            """, (path, url, clean_title, clean_artist))
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
                """, (clean_title, clean_artist, duration, duration, best_path, best_thumb, best_url, source, existing["id"]))
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
                """, (clean_title, clean_artist, duration, path, thumbnail, source, url, time.time()))

            conn.commit()

    def toggle_favorite_track(self, track_data):
        identifier = track_data.get("path") or track_data.get("url") or track_data.get("id")
        raw_url = track_data.get("url", "")
        title = str(track_data.get("title", "")).strip()
        artist = str(track_data.get("artist", "")).strip()

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
                    artist if artist else "Unknown",
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