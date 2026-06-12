from io import BytesIO
from typing import Tuple

import requests
from PIL import Image

from models import Song


class ApiService:
    def get_cover_url_from_itunes(self, song: Song) -> str:
        try:
            keyword = f"{song.title} {song.artist}"

            response = requests.get(
                "https://itunes.apple.com/search",
                params={
                    "term": keyword,
                    "media": "music",
                    "entity": "song",
                    "limit": 1
                },
                timeout=8
            )

            if response.status_code != 200:
                return ""

            data = response.json()
            results = data.get("results", [])

            if not results:
                return ""

            cover_url = results[0].get("artworkUrl100", "")

            if cover_url:
                cover_url = cover_url.replace("100x100bb", "300x300bb")

            return cover_url

        except Exception:
            return ""

    def get_lyrics_from_api(self, song: Song) -> str:
        try:
            if not song.artist or song.artist == "Chưa xác định":
                return "Không thể tìm lời bài hát vì chưa xác định được nghệ sĩ."

            url = f"https://api.lyrics.ovh/v1/{song.artist}/{song.title}"

            response = requests.get(url, timeout=8)

            if response.status_code != 200:
                return "Không tìm thấy lời bài hát từ API."

            data = response.json()
            lyrics = data.get("lyrics", "")

            if not lyrics.strip():
                return "API không trả về lời bài hát."

            return lyrics

        except Exception:
            return "Không thể kết nối API lời bài hát."

    def download_cover_image(self, cover_url: str):
        try:
            if not cover_url:
                return None

            response = requests.get(cover_url, timeout=8)

            if response.status_code != 200:
                return None

            image_data = BytesIO(response.content)
            image = Image.open(image_data)
            image = image.resize((180, 180))

            return image

        except Exception:
            return None

    def fetch_song_api_data(self, song: Song) -> Tuple[str, str]:
        lyrics = self.get_lyrics_from_api(song)
        cover_url = self.get_cover_url_from_itunes(song)

        return lyrics, cover_url