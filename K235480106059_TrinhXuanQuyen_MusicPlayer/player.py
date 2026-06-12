import os
from typing import Optional

import pygame

from models import Song


class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_song: Optional[Song] = None
        self.is_paused = False

    def play(self, song: Song):
        if not os.path.exists(song.file_path):
            raise FileNotFoundError("File nhạc không tồn tại.")

        pygame.mixer.music.load(song.file_path)
        pygame.mixer.music.play()

        self.current_song = song
        self.is_paused = False

    def pause_or_resume(self) -> str:
        if self.current_song is None:
            return "NO_SONG"

        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            return "RESUMED"

        pygame.mixer.music.pause()
        self.is_paused = True
        return "PAUSED"

    def stop(self):
        pygame.mixer.music.stop()
        self.is_paused = False