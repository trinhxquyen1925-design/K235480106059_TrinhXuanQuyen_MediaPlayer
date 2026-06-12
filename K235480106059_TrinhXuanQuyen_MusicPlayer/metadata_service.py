import os

from mutagen import File

from models import Song


class MetadataService:
    def read_metadata(self, file_path: str) -> Song:
        file_name = os.path.basename(file_path)
        default_title = os.path.splitext(file_name)[0]

        title = default_title
        artist = "Chưa xác định"
        album = "Chưa xác định"

        try:
            audio = File(file_path, easy=True)

            if audio is not None and audio.tags is not None:
                title_list = audio.tags.get("title")
                artist_list = audio.tags.get("artist")
                album_list = audio.tags.get("album")

                if title_list:
                    title = title_list[0]

                if artist_list:
                    artist = artist_list[0]

                if album_list:
                    album = album_list[0]

        except Exception:
            pass

        return Song(
            song_id=None,
            title=title,
            artist=artist,
            album=album,
            file_path=file_path
        )