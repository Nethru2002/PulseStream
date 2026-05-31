import os
import threading
import asyncio
import pygame
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.player import AudioPlayer
from core.recorder import AudioRecorder
from services.recognizer import SongRecognizer
from services.searcher import StreamSearcher
from ui.components import SidebarButton, TrackRow
from utils.helpers import ensure_dir

ctk.set_appearance_mode("Dark")

class PulseStreamApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PulseStream Pro")
        self.geometry("1300x850")
        self.configure(fg_color="#000000")

        ensure_dir("cache")
        self.player = AudioPlayer()
        self.recorder = AudioRecorder()
        self.recognizer = SongRecognizer()
        self.searcher = StreamSearcher()
        self.playlist_data = []

        self.setup_layout()

    def setup_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)    
        self.grid_rowconfigure(1, weight=0)    

        self.sidebar = ctk.CTkFrame(self, width=250, fg_color="#000000", corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="PULSE", font=("Inter", 28, "bold"), text_color="#1DB954").pack(pady=(60, 40))
        
        SidebarButton(self.sidebar, "Home", "🏠", None).pack(fill="x", padx=20, pady=5)
        SidebarButton(self.sidebar, "My Library", "📂", self.add_files).pack(fill="x", padx=20, pady=5)
        SidebarButton(self.sidebar, "Identify", "🎙", self.identify_song).pack(fill="x", padx=20, pady=5)

        self.main_view = ctk.CTkFrame(self, fg_color="#121212", corner_radius=25)
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=(20, 10))

        header = ctk.CTkFrame(self.main_view, fg_color="transparent")
        header.pack(fill="x", padx=50, pady=(50, 20))
        ctk.CTkLabel(header, text="Explore Music", font=("Inter", 26, "bold")).pack(side="left")
        
        self.search_entry = ctk.CTkEntry(
            self.main_view, 
            placeholder_text="What do you want to listen to?", 
            width=550, height=50, corner_radius=25, border_width=0, 
            fg_color="#1F1F1F", font=("Inter", 13)
        )
        self.search_entry.pack(anchor="w", padx=50, pady=10)
        self.search_entry.bind("<Return>", lambda e: self.handle_search())

        ctk.CTkLabel(self.main_view, text="Your Tracks", font=("Inter", 18, "bold")).pack(anchor="w", padx=60, pady=(30, 10))
        self.track_scroll = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        self.track_scroll.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        player_container = ctk.CTkFrame(self, fg_color="transparent", height=130)
        player_container.grid(row=1, column=1, sticky="ew")
        player_container.grid_propagate(False)

        self.player_bar = ctk.CTkFrame(
            player_container, height=95, fg_color="#181818", 
            corner_radius=40, border_width=1, border_color="#282828"
        )
        self.player_bar.place(relx=0.5, rely=0.4, anchor="center", relwidth=0.85)
        self.player_bar.pack_propagate(False)

        meta = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        meta.pack(side="left", padx=40)
        self.now_title = ctk.CTkLabel(meta, text="Not Playing", font=("Inter", 14, "bold"), text_color="white")
        self.now_title.pack(anchor="w")
        self.now_artist = ctk.CTkLabel(meta, text="---", font=("Inter", 11), text_color="#A7A7A7")
        self.now_artist.pack(anchor="w")

        ctrls = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        ctrls.place(relx=0.5, rely=0.5, anchor="center")
        
        self.play_btn = ctk.CTkButton(
            ctrls, text="▶", width=58, height=58, corner_radius=29,
            fg_color="white", text_color="black", font=("Arial", 22, "bold"),
            command=self.play_logic
        )
        self.play_btn.pack(side="left", padx=20)
        
        ctk.CTkButton(
            ctrls, text="⏸", width=40, height=40, fg_color="transparent", 
            text_color="white", font=("Arial", 18),
            command=self.player.toggle_pause
        ).pack(side="left")

        vol_frame = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        vol_frame.pack(side="right", padx=40)
        ctk.CTkLabel(vol_frame, text="🔊", font=("Arial", 11)).pack(side="left", padx=10)
        self.vol_slider = ctk.CTkSlider(
            vol_frame, width=120, height=16, fg_color="#333333", 
            progress_color="#1DB954", command=self.player.set_volume
        )
        self.vol_slider.pack(side="left")
        self.vol_slider.set(0.7)

    def handle_search(self):
        query = self.search_entry.get()
        if not query: return
        self.search_entry.delete(0, 'end')
        
        def task():
            try:
                data = self.searcher.download_and_get_path(query)
                self.playlist_data.append(data)
                self.after(0, lambda: self.render_track(data, "STREAM"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=task, daemon=True).start()

    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio", "*.mp3 *.wav *.ogg")])
        for f in files:
            data = {"title": os.path.basename(f), "artist": "Local File", "path": f}
            self.playlist_data.append(data)
            self.render_track(data, "LOCAL")

    def render_track(self, data, tag):
        TrackRow(self.track_scroll, data['title'], data.get('artist', 'Artist'), 
                 tag, lambda: self.start_play(data)).pack(fill="x", pady=2)

    def start_play(self, data):
        self.player.play(data['path'])
        self.now_title.configure(text=data['title'][:35] + "...")
        self.now_artist.configure(text=data.get('artist', 'Unknown Artist'))

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
                    self.after(0, lambda: messagebox.showinfo("Found!", f"{result['track']['title']}\n{result['track']['subtitle']}"))
            finally:
                if os.path.exists(temp): os.remove(temp)
        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    app = PulseStreamApp()
    app.mainloop()