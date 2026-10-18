import sqlite3
import os
import time

class DatabaseManager:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self._init_db()

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
                    created_at REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_path TEXT NOT NULL,
                    played_at REAL
                )
            """)
            conn.commit()

    def add_or_update_track(self, title, artist, duration, path, thumbnail="", source="LOCAL"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tracks (title, artist, duration, path, thumbnail, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    title=excluded.title,
                    artist=excluded.artist,
                    duration=excluded.duration,
                    thumbnail=CASE WHEN excluded.thumbnail != '' THEN excluded.thumbnail ELSE tracks.thumbnail END
            """, (title, artist, duration, path, thumbnail, source, time.time()))
            conn.commit()

    def toggle_favorite_track(self, track_data):
        identifier = track_data.get("path") or track_data.get("url") or track_data.get("id")
        if not identifier:
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_favorite FROM tracks WHERE path = ?", (identifier,))
            row = cursor.fetchone()

            if row:
                new_state = 0 if row["is_favorite"] == 1 else 1
                cursor.execute("UPDATE tracks SET is_favorite = ? WHERE path = ?", (new_state, identifier))
                conn.commit()
                return new_state == 1
            else:
                cursor.execute("""
                    INSERT INTO tracks (title, artist, duration, path, thumbnail, source, is_favorite, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """, (
                    track_data.get("title", "Unknown"),
                    track_data.get("artist", "Unknown"),
                    track_data.get("duration", 0),
                    identifier,
                    track_data.get("thumbnail", ""),
                    track_data.get("source", "STREAM"),
                    time.time()
                ))
                conn.commit()
                return True

    def toggle_favorite(self, path):
        if not path:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_favorite FROM tracks WHERE path = ?", (path,))
            row = cursor.fetchone()
            if row:
                new_state = 0 if row["is_favorite"] == 1 else 1
                cursor.execute("UPDATE tracks SET is_favorite = ? WHERE path = ?", (new_state, path))
                conn.commit()
                return new_state == 1
            return False

    def is_favorite(self, path_or_url):
        if not path_or_url:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_favorite FROM tracks WHERE path = ?", (path_or_url,))
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
            cursor.execute("SELECT * FROM tracks WHERE is_favorite = 1 ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_history(self, limit=50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.*, h.played_at 
                FROM history h
                JOIN tracks t ON h.track_path = t.path
                ORDER BY h.played_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_saved(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tracks ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]