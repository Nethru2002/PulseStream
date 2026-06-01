import os
import threading
import asyncio
import pygame
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
from mutagen.mp3 import MP3
from core.player import AudioPlayer
from core.recorder import AudioRecorder
from services.recognizer import SongRecognizer
from services.searcher import StreamSearcher
from ui.styles import AppStyles
from ui.components import SidebarButton, TrackRow, ModernSearchArea
from utils.helpers import ensure_dir

ctk.set_appearance_mode("Dark")

class PulseStreamApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PulseStream Pro")
        self.geometry("1280x920")
        self.configure(fg_color="#000000")
        ensure_dir("cache")
        self.player = AudioPlayer()
        self.recorder = AudioRecorder()
        self.recognizer = SongRecognizer()
        self.searcher = StreamSearcher()
        self.playlist_data = []
        self.current_song_data = None
        self.is_seeking = False
        self.song_duration = 0
        self.setup_layout()
        self.update_ui_loop()
        self.after(500, lambda: self.logo_lbl.focus_set())

    def setup_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color="#000000", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.logo_lbl = ctk.CTkLabel(self.sidebar, text="PULSE", font=("Inter", 28, "bold"), text_color="#1DB954")
        self.logo_lbl.pack(pady=60)
        SidebarButton(self.sidebar, "Home", "🏠", None).pack(fill="x", padx=20, pady=5)
        SidebarButton(self.sidebar, "Library", "📂", self.add_files).pack(fill="x", padx=20, pady=5)
        SidebarButton(self.sidebar, "Identify Song", "🎙", self.identify_song).pack(fill="x", padx=20, pady=5)
        self.main_frame = ctk.CTkFrame(self, fg_color="#121212", corner_radius=25)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x", padx=50, pady=(40, 10))
        ctk.CTkLabel(header, text="Explore Music", font=("Inter", 28, "bold")).pack(side="left")
        self.search_area = ModernSearchArea(self.main_frame, self.handle_search)
        self.search_area.pack(fill="x", padx=50, pady=20)
        self.track_scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.track_scroll.pack(fill="both", expand=True, padx=40, pady=(0, 120))
        self.player_bar = ctk.CTkFrame(self.main_frame, height=120, fg_color="#181818", 
                                       corner_radius=30, border_width=1, border_color="#282828", bg_color="#121212")
        self.player_bar.place(relx=0.5, rely=0.9, anchor="center", relwidth=0.9)
        self.player_bar.pack_propagate(False)
        self.progress_slider = ctk.CTkSlider(self.player_bar, from_=0, to=100, height=16, 
                                             progress_color="#1DB954", fg_color="#333333", bg_color="#181818")
        self.progress_slider.pack(fill="x", padx=60, pady=(15, 0))
        self.progress_slider.set(0)
        self.progress_slider.bind("<Button-1>", lambda e: setattr(self, 'is_seeking', True))
        self.progress_slider.bind("<ButtonRelease-1>", self._on_slider_release)
        content_ctrls = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        content_ctrls.pack(fill="both", expand=True, padx=40)
        self.now_title = ctk.CTkLabel(content_ctrls, text="Not Playing", font=("Inter", 13, "bold"), text_color="white")
        self.now_title.pack(side="left", padx=10)
        mid_ctrls = ctk.CTkFrame(content_ctrls, fg_color="transparent")
        mid_ctrls.place(relx=0.5, rely=0.5, anchor="center")
        self.play_btn = ctk.CTkButton(mid_ctrls, text="▶", width=56, height=56, corner_radius=28, 
                                      fg_color="white", text_color="black", font=("Arial", 20, "bold"), command=self.play_logic)
        self.play_btn.pack(side="left", padx=15)
        ctk.CTkButton(mid_ctrls, text="⏸", width=40, height=40, fg_color="transparent", 
                      text_color="white", font=("Arial", 18), command=self.player.toggle_pause).pack(side="left")
        vol_frame = ctk.CTkFrame(content_ctrls, fg_color="transparent")
        vol_frame.pack(side="right", padx=10)
        ctk.CTkLabel(vol_frame, text="🔊", font=("Arial", 12)).pack(side="left", padx=5)
        self.vol_slider = ctk.CTkSlider(vol_frame, width=110, height=16, progress_color="#1DB954", command=self.player.set_volume)
        self.vol_slider.pack(side="left")
        self.vol_slider.set(0.7)

    def handle_search(self, query_override=None):
        query = query_override if query_override else self.search_area.get()
        if not query: return
        self.search_area.set_text(query)
        self.search_area.set_state("disabled")
        def task():
            try:
                data = self.searcher.download_and_get_path(query)
                self.playlist_data.append(data)
                self.after(0, self.refresh_list)
                self.after(0, lambda: self.search_area.set_state("normal"))
            except Exception as e:
                self.after(0, lambda: self.search_area.set_state("normal"))
                messagebox.showerror("Error", str(e))
        threading.Thread(target=task, daemon=True).start()

    def refresh_list(self):
        for child in self.track_scroll.winfo_children(): child.destroy()
        for item in self.playlist_data:
            tag = "STREAM" if "cache" in item['path'] else "LOCAL"
            TrackRow(self.track_scroll, item, tag, lambda i=item: self.start_play(i), 
                     lambda i=item: self.save_track(i), self.move_to_front, self.move_to_back).pack(fill="x", pady=2)

    def move_to_front(self, d): self.playlist_data.remove(d); self.playlist_data.insert(0, d); self.refresh_list()
    def move_to_back(self, d): self.playlist_data.remove(d); self.playlist_data.append(d); self.refresh_list()
    
    def start_play(self, data):
        self.current_song_data = data
        try:
            audio = MP3(data['path'])
            self.song_duration = audio.info.length
        except: self.song_duration = 300
        self.progress_slider.configure(to=self.song_duration)
        self.progress_slider.set(0)
        self.player.play(data['path'])
        self.now_title.configure(text=data['title'][:30] + "...")

    def _on_slider_release(self, event):
        self.is_seeking = False
        if self.current_song_data:
            pygame.mixer.music.play(start=self.progress_slider.get())

    def update_ui_loop(self):
        if pygame.mixer.music.get_busy() and not self.is_seeking:
            self.progress_slider.set(self.progress_slider.get() + 0.5)
        self.after(500, self.update_ui_loop)

    def add_files(self):
        f = filedialog.askopenfilenames()
        for x in f: self.playlist_data.append({"title": os.path.basename(x), "path": x})
        self.refresh_list()

    def save_track(self, d):
        p = filedialog.asksaveasfilename(defaultextension=".mp3", initialfile=f"{d['title']}.mp3")
        if p: shutil.copy(d['path'], p)

    def play_logic(self):
        if self.player.is_paused: self.player.toggle_pause()
        elif self.playlist_data: self.start_play(self.playlist_data[0])

    def identify_song(self):
        messagebox.showinfo("Pulse", "Listening for 7 seconds...")
        def task():
            temp = "id_cache.wav"
            try:
                self.recorder.record(temp)
                result = asyncio.run(self.recognizer.identify(temp))
                if 'track' in result:
                    title = result['track']['title']
                    artist = result['track']['subtitle']
                    query = f"{title} {artist}"
                    if messagebox.askyesno("Song Found!", f"🎵 {title}\n👤 {artist}\n\nWould you like to stream this song now?"):
                        self.after(0, lambda: self.handle_search(query))
                else:
                    messagebox.showwarning("No Match", "Could not identify that song.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                if os.path.exists(temp): os.remove(temp)
        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    app = PulseStreamApp()
    app.mainloop()