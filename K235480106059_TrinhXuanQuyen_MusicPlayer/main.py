import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from typing import Optional

import pygame
from PIL import ImageTk, Image
from mutagen import File as MutagenFile

from api_service import ApiService
from database import MusicDatabase
from metadata_service import MetadataService
from models import Playlist, Song
from player import MusicPlayer


class MusicPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Media Player - Trịnh Xuân Quyền")
        self.root.geometry("1320x780")
        self.root.resizable(False, False)
        self.root.configure(bg="#e0f2fe")

        self.database = MusicDatabase()
        self.metadata_service = MetadataService()
        self.api_service = ApiService()
        self.playlist = Playlist()
        self.player = MusicPlayer()

        self.selected_song: Optional[Song] = None
        self.cover_photo = None

        self.song_duration = 0
        self.seek_offset = 0
        self.is_dragging_seek = False
        self.manual_stopped = False
        self.is_auto_next_running = False

        self.setup_style()
        self.create_widgets()
        self.load_songs()
        self.update_progress_loop()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Sky.Treeview",
            font=("Segoe UI", 10),
            rowheight=34,
            background="#ffffff",
            foreground="#0f172a",
            fieldbackground="#ffffff",
            borderwidth=0
        )

        style.map(
            "Sky.Treeview",
            background=[("selected", "#0ea5e9")],
            foreground=[("selected", "#ffffff")]
        )

        style.configure(
            "Sky.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#bae6fd",
            foreground="#075985",
            relief="flat"
        )

        style.configure(
            "Sky.Horizontal.TScale",
            background="#ffffff",
            troughcolor="#bae6fd"
        )

    def create_widgets(self):
        header = tk.Frame(self.root, bg="#0ea5e9", height=88)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="PYTHON MEDIA PLAYER",
            bg="#0ea5e9",
            fg="#ffffff",
            font=("Segoe UI", 27, "bold")
        )
        title.place(x=32, y=14)

        subtitle = tk.Label(
            header,
            text="Quản lý danh sách phát  |  Phát nhạc  |  Lời bài hát  |  Ảnh bìa album  |  SQLite Database  |  Trịnh Xuân Quyền - K235480106059",
            bg="#0ea5e9",
            fg="#f0f9ff",
            font=("Segoe UI", 11, "bold")
        )
        subtitle.place(x=38, y=58)

        main = tk.Frame(self.root, bg="#e0f2fe")
        main.pack(fill="both", expand=True, padx=22, pady=18)

        # =========================
        # DANH SÁCH PHÁT
        # =========================

        playlist_card = tk.Frame(
            main,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#7dd3fc"
        )
        playlist_card.place(x=0, y=0, width=330, height=620)

        playlist_title = tk.Label(
            playlist_card,
            text="Danh sách phát",
            bg="#ffffff",
            fg="#075985",
            font=("Segoe UI", 19, "bold")
        )
        playlist_title.place(x=20, y=18)

        playlist_note = tk.Label(
            playlist_card,
            text="Danh sách bài hát đã lưu trong SQLite",
            bg="#ffffff",
            fg="#64748b",
            font=("Segoe UI", 10)
        )
        playlist_note.place(x=22, y=54)

        table_frame = tk.Frame(playlist_card, bg="#ffffff")
        table_frame.place(x=16, y=86, width=298, height=415)

        columns = ("stt", "title", "artist")
        self.song_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=12,
            style="Sky.Treeview"
        )

        self.song_table.heading("stt", text="STT")
        self.song_table.heading("title", text="Tên bài")
        self.song_table.heading("artist", text="Nghệ sĩ")

        self.song_table.column("stt", width=38, anchor="center")
        self.song_table.column("title", width=138)
        self.song_table.column("artist", width=112)

        table_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.song_table.yview
        )
        self.song_table.configure(yscrollcommand=table_scroll.set)

        self.song_table.pack(side="left", fill="both", expand=True)
        table_scroll.pack(side="right", fill="y")

        self.song_table.bind("<<TreeviewSelect>>", self.on_song_select)

        button_area = tk.Frame(playlist_card, bg="#ffffff")
        button_area.place(x=16, y=515, width=298, height=82)

        self.create_text_button(button_area, "THÊM", "#0ea5e9", 0, 0, 140, self.add_song)
        self.create_text_button(button_area, "XÓA", "#ef4444", 158, 0, 140, self.delete_song)
        self.create_text_button(button_area, "TẢI LỜI & ẢNH", "#0284c7", 0, 45, 140, self.fetch_api_data)
        self.create_text_button(button_area, "LÀM MỚI", "#475569", 158, 45, 140, self.load_songs)

        # =========================
        # ĐANG PHÁT
        # =========================

        player_card = tk.Frame(
            main,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#7dd3fc"
        )
        player_card.place(x=352, y=0, width=420, height=620)

        now_title = tk.Label(
            player_card,
            text="Đang phát",
            bg="#ffffff",
            fg="#075985",
            font=("Segoe UI", 19, "bold")
        )
        now_title.place(x=24, y=18)

        cover_box = tk.Frame(player_card, bg="#e0f2fe", bd=0)
        cover_box.place(x=60, y=68, width=300, height=300)

        self.cover_label = tk.Label(
            cover_box,
            text="ALBUM\nCOVER",
            bg="#e0f2fe",
            fg="#0284c7",
            font=("Segoe UI", 19, "bold"),
            justify="center"
        )
        self.cover_label.pack(fill="both", expand=True, padx=10, pady=10)

        self.current_song_label = tk.Label(
            player_card,
            text="Chưa phát bài hát",
            bg="#ffffff",
            fg="#0f172a",
            font=("Segoe UI", 14, "bold"),
            wraplength=350,
            justify="center"
        )
        self.current_song_label.place(x=30, y=378, width=360, height=58)

        self.artist_album_label = tk.Label(
            player_card,
            text="Nghệ sĩ: --\nAlbum: --",
            bg="#ffffff",
            fg="#64748b",
            font=("Segoe UI", 10),
            wraplength=350,
            justify="center"
        )
        self.artist_album_label.place(x=32, y=440, width=356, height=42)

        seek_frame = tk.Frame(player_card, bg="#ffffff")
        seek_frame.place(x=38, y=500, width=344, height=60)

        self.seek_scale = ttk.Scale(
            seek_frame,
            from_=0,
            to=100,
            orient="horizontal",
            style="Sky.Horizontal.TScale",
            command=self.on_seek_drag
        )
        self.seek_scale.place(x=0, y=5, width=344)

        self.seek_scale.bind("<ButtonPress-1>", self.start_seek_drag)
        self.seek_scale.bind("<ButtonRelease-1>", self.stop_seek_drag)

        self.time_label = tk.Label(
            seek_frame,
            text="00:00 / 00:00",
            bg="#ffffff",
            fg="#0284c7",
            font=("Segoe UI", 10, "bold")
        )
        self.time_label.place(x=0, y=34, width=344)

        control_frame = tk.Frame(player_card, bg="#ffffff")
        control_frame.place(x=35, y=565, width=350, height=48)

        self.create_control_button(control_frame, "PHÁT", "#0ea5e9", 0, self.play_song, width=78)
        self.create_control_button(control_frame, "TẠM DỪNG", "#f59e0b", 88, self.pause_resume_song, width=112)
        self.create_control_button(control_frame, "DỪNG", "#ef4444", 210, self.stop_song, width=78)
        self.create_control_button(control_frame, "TIẾP", "#0284c7", 298, self.next_song, width=52)

        # =========================
        # THÔNG TIN + LỜI BÀI HÁT
        # =========================

        lyrics_card = tk.Frame(
            main,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#7dd3fc"
        )
        lyrics_card.place(x=794, y=0, width=482, height=620)

        info_title = tk.Label(
            lyrics_card,
            text="Thông tin bài hát",
            bg="#ffffff",
            fg="#075985",
            font=("Segoe UI", 19, "bold")
        )
        info_title.place(x=22, y=18)

        self.info_label = tk.Label(
            lyrics_card,
            text="Tên bài hát: --\nNghệ sĩ: --\nAlbum: --",
            bg="#eff6ff",
            fg="#0f172a",
            font=("Segoe UI", 11),
            justify="left",
            anchor="nw",
            wraplength=405
        )
        self.info_label.place(x=22, y=62, width=438, height=72)

        lyrics_title = tk.Label(
            lyrics_card,
            text="Lời bài hát",
            bg="#ffffff",
            fg="#075985",
            font=("Segoe UI", 19, "bold")
        )
        lyrics_title.place(x=22, y=152)

        lyrics_note = tk.Label(
            lyrics_card,
            text="Lời bài hát được lấy từ API",
            bg="#ffffff",
            fg="#64748b",
            font=("Segoe UI", 10)
        )
        lyrics_note.place(x=24, y=190)

        lyrics_frame = tk.Frame(
            lyrics_card,
            bg="#ffffff",
            bd=1,
            relief="solid"
        )
        lyrics_frame.place(x=22, y=220, width=438, height=365)

        self.lyrics_text = tk.Text(
            lyrics_frame,
            font=("Segoe UI", 11),
            wrap="word",
            bg="#ffffff",
            fg="#0f172a",
            bd=0,
            padx=14,
            pady=12
        )

        lyrics_scroll = ttk.Scrollbar(
            lyrics_frame,
            orient="vertical",
            command=self.lyrics_text.yview
        )
        self.lyrics_text.configure(yscrollcommand=lyrics_scroll.set)

        self.lyrics_text.pack(side="left", fill="both", expand=True)
        lyrics_scroll.pack(side="right", fill="y")

        footer = tk.Label(
            self.root,
            text="Python Media Player  |  Tkinter GUI  |  SQLite Database  |  pygame  |  Lyrics API  |  Album Cover API",
            bg="#e0f2fe",
            fg="#64748b",
            font=("Segoe UI", 10)
        )
        footer.pack(side="bottom", pady=(0, 8))

    # =========================
    # BUTTON
    # =========================

    def create_text_button(self, parent, text, bg, x, y, width, command):
        button = tk.Button(
            parent,
            text=text,
            bg=bg,
            fg="#ffffff",
            activebackground=bg,
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            relief="flat",
            cursor="hand2",
            command=command
        )
        button.place(x=x, y=y, width=width, height=36)
        return button

    def create_control_button(self, parent, text, bg, x, command, width=78):
        button = tk.Button(
            parent,
            text=text,
            bg=bg,
            fg="#ffffff",
            activebackground=bg,
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            relief="flat",
            cursor="hand2",
            command=command
        )
        button.place(x=x, y=0, width=width, height=42)
        return button

    # =========================
    # DATABASE / PLAYLIST
    # =========================

    def load_songs(self):
        for item in self.song_table.get_children():
            self.song_table.delete(item)

        songs = self.database.get_all_songs()
        self.playlist.set_songs(songs)

        for index, song in enumerate(songs, start=1):
            self.song_table.insert(
                "",
                "end",
                values=(index, song.title, song.artist)
            )

    def add_song(self):
        file_paths = filedialog.askopenfilenames(
            title="Chọn file nhạc",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.ogg *.flac"),
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav"),
                ("All Files", "*.*")
            ]
        )

        if not file_paths:
            return

        added_count = 0
        duplicate_count = 0

        for file_path in file_paths:
            song = self.metadata_service.read_metadata(file_path)
            success = self.database.add_song(song)

            if success:
                added_count += 1
            else:
                duplicate_count += 1

        self.load_songs()

        messagebox.showinfo(
            "Kết quả",
            f"Thêm thành công: {added_count} bài hát\nBị trùng: {duplicate_count} bài hát"
        )

    def delete_song(self):
        song = self.get_selected_song()

        if song is None:
            messagebox.showwarning("Thông báo", "Vui lòng chọn bài hát cần xóa.")
            return

        confirm = messagebox.askyesno(
            "Xác nhận",
            f"Bạn có chắc muốn xóa bài hát:\n{song.title}?"
        )

        if confirm:
            self.database.delete_song(song.song_id)
            self.selected_song = None
            self.load_songs()
            self.reset_display()
            messagebox.showinfo("Thành công", "Đã xóa bài hát khỏi danh sách phát.")

    def reset_display(self):
        self.current_song_label.config(text="Chưa phát bài hát")
        self.artist_album_label.config(text="Nghệ sĩ: --\nAlbum: --")
        self.info_label.config(text="Tên bài hát: --\nNghệ sĩ: --\nAlbum: --")
        self.lyrics_text.delete("1.0", tk.END)
        self.cover_label.config(image="", text="ALBUM\nCOVER", bg="#e0f2fe")
        self.cover_label.image = None
        self.cover_photo = None
        self.seek_scale.set(0)
        self.time_label.config(text="00:00 / 00:00")

    # =========================
    # SONG SELECT / DETAIL
    # =========================

    def on_song_select(self, event):
        selected_items = self.song_table.selection()

        if not selected_items:
            return

        item = selected_items[0]
        index = self.song_table.index(item)

        if index < 0 or index >= len(self.playlist.songs):
            return

        song = self.playlist.songs[index]
        self.selected_song = song

        # Chỉ cập nhật phần bên phải, không đổi bài đang phát ở giữa
        self.show_selected_song_detail(song)

    def get_selected_song(self):
        return self.selected_song

    def show_selected_song_detail(self, song: Song):
        self.info_label.config(
            text=(
                f"Tên bài hát: {song.title}\n"
                f"Nghệ sĩ: {song.artist}\n"
                f"Album: {song.album}"
            )
        )

        self.lyrics_text.delete("1.0", tk.END)

        if song.lyrics:
            self.lyrics_text.insert(tk.END, song.lyrics)
        else:
            self.lyrics_text.insert(
                tk.END,
                "Chưa có lời bài hát.\n\nBấm nút “TẢI LỜI & ẢNH” để lấy lời bài hát và ảnh bìa album từ API."
            )

    def show_playing_song(self, song: Song):
        self.current_song_label.config(text=song.title)

        self.artist_album_label.config(
            text=(
                f"Nghệ sĩ: {song.artist}\n"
                f"Album: {song.album}"
            )
        )

        self.show_cover(song.cover_url)

    def show_cover(self, cover_url: str):
        image = self.api_service.download_cover_image(cover_url)

        if image is None:
            self.cover_label.config(
                image="",
                text="ALBUM\nCOVER",
                bg="#e0f2fe"
            )
            self.cover_label.image = None
            self.cover_photo = None
            return

        image = image.convert("RGB")
        image = image.resize((280, 280), Image.LANCZOS)

        self.cover_photo = ImageTk.PhotoImage(image)
        self.cover_label.config(image=self.cover_photo, text="", bg="#e0f2fe")
        self.cover_label.image = self.cover_photo

    # =========================
    # PLAYER
    # =========================

    def set_playlist_index_by_song(self, song: Song):
        for index, item in enumerate(self.playlist.songs):
            if item.song_id == song.song_id:
                self.playlist.set_current_index(index)
                return

    def play_song(self):
        song = self.get_selected_song()

        if song is None:
            song = self.playlist.get_current_song()

        if song is None:
            messagebox.showwarning("Thông báo", "Vui lòng chọn một bài hát.")
            return

        try:
            self.set_playlist_index_by_song(song)
            self.player.play(song)
            self.song_duration = self.get_audio_duration(song.file_path)
            self.seek_offset = 0
            self.manual_stopped = False
            self.is_auto_next_running = False

            self.show_playing_song(song)
            self.seek_scale.set(0)
            self.time_label.config(text=f"00:00 / {self.format_time(self.song_duration)}")

        except FileNotFoundError:
            messagebox.showerror("Lỗi", "File nhạc không tồn tại.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể phát bài hát.\nChi tiết: {e}")

    def pause_resume_song(self):
        result = self.player.pause_or_resume()

        if result == "NO_SONG":
            messagebox.showwarning("Thông báo", "Chưa có bài hát nào đang phát.")
        elif result == "PAUSED":
            self.current_song_label.config(text="Đã tạm dừng")
        elif result == "RESUMED":
            song = self.player.current_song
            if song is not None:
                self.current_song_label.config(text=song.title)

    def stop_song(self):
        self.player.stop()
        self.manual_stopped = True
        self.is_auto_next_running = False
        self.seek_offset = 0
        self.seek_scale.set(0)
        self.time_label.config(text=f"00:00 / {self.format_time(self.song_duration)}")

    def next_song(self):
        song = self.playlist.next_song()

        if song is None:
            messagebox.showwarning("Thông báo", "Danh sách phát đang trống.")
            return

        self.selected_song = song
        self.show_selected_song_detail(song)

        try:
            self.player.play(song)
            self.song_duration = self.get_audio_duration(song.file_path)
            self.seek_offset = 0
            self.manual_stopped = False
            self.is_auto_next_running = False

            self.show_playing_song(song)
            self.seek_scale.set(0)
            self.time_label.config(text=f"00:00 / {self.format_time(self.song_duration)}")

            children = self.song_table.get_children()
            if 0 <= self.playlist.current_index < len(children):
                self.song_table.selection_set(children[self.playlist.current_index])
                self.song_table.focus(children[self.playlist.current_index])

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể phát bài tiếp theo.\nChi tiết: {e}")

    # =========================
    # SEEK / TIME / AUTO NEXT
    # =========================

    def start_seek_drag(self, event):
        self.is_dragging_seek = True

    def stop_seek_drag(self, event):
        self.is_dragging_seek = False

        if self.player.current_song is None or self.song_duration <= 0:
            return

        percent = self.seek_scale.get()
        target_seconds = int((percent / 100) * self.song_duration)

        try:
            pygame.mixer.music.play(start=target_seconds)
            self.seek_offset = target_seconds
            self.manual_stopped = False
            self.is_auto_next_running = False

            self.time_label.config(
                text=f"{self.format_time(target_seconds)} / {self.format_time(self.song_duration)}"
            )
        except Exception:
            messagebox.showwarning(
                "Thông báo",
                "File nhạc hiện tại không hỗ trợ tua chính xác. Chức năng tua hoạt động tốt nhất với file MP3 chuẩn."
            )

    def on_seek_drag(self, value):
        if not self.is_dragging_seek or self.song_duration <= 0:
            return

        percent = float(value)
        preview_seconds = int((percent / 100) * self.song_duration)

        self.time_label.config(
            text=f"{self.format_time(preview_seconds)} / {self.format_time(self.song_duration)}"
        )

    def get_audio_duration(self, file_path: str) -> int:
        try:
            audio = MutagenFile(file_path)
            if audio is not None and audio.info is not None:
                return int(audio.info.length)
        except Exception:
            pass

        return 0

    def update_progress_loop(self):
        try:
            current_song = self.player.current_song

            if current_song is not None and self.song_duration > 0 and not self.is_dragging_seek:
                current_ms = pygame.mixer.music.get_pos()

                if current_ms >= 0:
                    current_sec = self.seek_offset + int(current_ms / 1000)

                    if current_sec <= self.song_duration:
                        percent = (current_sec / self.song_duration) * 100
                        self.seek_scale.set(percent)

                        self.time_label.config(
                            text=f"{self.format_time(current_sec)} / {self.format_time(self.song_duration)}"
                        )

                    if (
                        current_sec >= self.song_duration - 1
                        and not self.player.is_paused
                        and not self.manual_stopped
                        and not self.is_auto_next_running
                    ):
                        self.is_auto_next_running = True
                        self.root.after(800, self.next_song)

        except Exception:
            pass

        self.root.after(500, self.update_progress_loop)

    def format_time(self, seconds: int) -> str:
        if seconds < 0:
            seconds = 0

        minutes = seconds // 60
        secs = seconds % 60

        return f"{minutes:02d}:{secs:02d}"

    # =========================
    # API
    # =========================

    def fetch_api_data(self):
        song = self.get_selected_song()

        if song is None:
            messagebox.showwarning("Thông báo", "Vui lòng chọn bài hát trước.")
            return

        self.info_label.config(
            text=(
                f"Tên bài hát: {song.title}\n"
                f"Nghệ sĩ: {song.artist}\n"
                f"Đang tải lời bài hát và ảnh bìa..."
            )
        )
        self.root.update_idletasks()

        lyrics, cover_url = self.api_service.fetch_song_api_data(song)

        self.database.update_song_api_data(
            song_id=song.song_id,
            lyrics=lyrics,
            cover_url=cover_url
        )

        song.lyrics = lyrics
        song.cover_url = cover_url

        self.show_selected_song_detail(song)

        if self.player.current_song is not None and self.player.current_song.song_id == song.song_id:
            self.show_playing_song(song)

        messagebox.showinfo("Thành công", "Đã lấy lời bài hát và ảnh bìa album từ API.")


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.mainloop()