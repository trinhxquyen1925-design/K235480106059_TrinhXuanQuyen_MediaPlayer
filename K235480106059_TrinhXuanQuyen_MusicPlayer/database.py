import sqlite3
from typing import List

from models import Song


class MusicDatabase:
    def __init__(self, db_name: str = "music_player.db"):
        self.db_name = db_name
        self.create_table()

    def connect(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT,
                album TEXT,
                file_path TEXT NOT NULL UNIQUE,
                lyrics TEXT,
                cover_url TEXT
            )
        """)

        conn.commit()
        conn.close()

    def add_song(self, song: Song) -> bool:
        try:
            conn = self.connect()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO songs (title, artist, album, file_path, lyrics, cover_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                song.title,
                song.artist,
                song.album,
                song.file_path,
                song.lyrics,
                song.cover_url
            ))

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError:
            return False

    def get_all_songs(self) -> List[Song]:
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, artist, album, file_path, lyrics, cover_url
            FROM songs
            ORDER BY id ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        songs = []

        for row in rows:
            songs.append(Song(
                song_id=row[0],
                title=row[1],
                artist=row[2],
                album=row[3],
                file_path=row[4],
                lyrics=row[5] or "",
                cover_url=row[6] or ""
            ))

        return songs

    def delete_song(self, song_id: int):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM songs WHERE id = ?", (song_id,))

        conn.commit()
        conn.close()

    def update_song_api_data(self, song_id: int, lyrics: str, cover_url: str):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE songs
            SET lyrics = ?, cover_url = ?
            WHERE id = ?
        """, (lyrics, cover_url, song_id))

        conn.commit()
        conn.close()