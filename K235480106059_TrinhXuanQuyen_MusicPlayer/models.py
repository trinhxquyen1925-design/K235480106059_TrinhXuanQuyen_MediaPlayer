from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Song:
    song_id: Optional[int]
    title: str
    artist: str
    album: str
    file_path: str
    lyrics: str = ""
    cover_url: str = ""

    def get_display_name(self) -> str:
        if self.artist and self.artist != "Chưa xác định":
            return f"{self.title} - {self.artist}"
        return self.title


class Playlist:
    def __init__(self):
        self.songs: List[Song] = []
        self.current_index: int = -1

    def set_songs(self, songs: List[Song]):
        self.songs = songs

        if len(self.songs) == 0:
            self.current_index = -1
        elif self.current_index == -1:
            self.current_index = 0

    def get_current_song(self) -> Optional[Song]:
        if 0 <= self.current_index < len(self.songs):
            return self.songs[self.current_index]
        return None

    def set_current_index(self, index: int):
        if 0 <= index < len(self.songs):
            self.current_index = index

    def next_song(self) -> Optional[Song]:
        if not self.songs:
            return None

        self.current_index += 1

        if self.current_index >= len(self.songs):
            self.current_index = 0

        return self.get_current_song()