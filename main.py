import os
import re
import random
import threading
import asyncio
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
from mutagen.mp3 import MP3

from core.player import AudioPlayer
from core.recorder import AudioRecorder
from services.recognizer import SongRecognizer
from services.searcher import StreamSearcher
from services.db import DatabaseManager
from services.lyrics import LyricsService
from ui.styles import AppStyles
from ui.components import (
    SidebarNavButton,
    TrackTableRow,
    ModernSearchArea,
    HeroBanner,
    AnimatedVisualizer,
    create_rounded_cover
)
from utils.helpers import ensure_dir, format_time, sanitize_filename

ctk.set_appearance_mode("Dark")

class PulseStreamStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PulseStream — High Definition Audio Studio")
        self.geometry("1420x960")
        self.minsize(1120, 740)
        self.configure(fg_color=AppStyles.BG_BASE)

        ensure_dir("cache")
        ensure_dir("cache/thumbs")

        self.db = DatabaseManager()
        self.player = AudioPlayer()
        self.recorder = AudioRecorder()
        self.recognizer = SongRecognizer()
        self.searcher = StreamSearcher()
        self.lyrics_service = LyricsService()

        self.queue = []
        self.current_track = None
        self.current_duration = 0
        self.is_seeking = False
        self.repeat_mode = "NONE"
        self.shuffle_mode = False
        self.current_tab = "EXPLORE"

        self.lyrics_data = {"type": "none", "text": "No live track selected."}
        self.active_lyric_index = -1
        self.is_drawer_visible = True

        self.setup_layout()
        self.refresh_sidebar_playlists()
        self.navigate("EXPLORE")
        self.start_main_clock()

    def setup_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=320)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0, minsize=92)

        self.sidebar = ctk.CTkScrollableFrame(
            self,
            width=240,
            fg_color=AppStyles.BG_SIDEBAR,
            corner_radius=0,
            border_width=1,
            border_color=AppStyles.BORDER_SUBTLE,
            scrollbar_button_color="#1E1E28",
            scrollbar_button_hover_color=AppStyles.ACCENT
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        brand_wrap = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_wrap.pack(fill="x", padx=16, pady=(18, 16))
        ctk.CTkLabel(
            brand_wrap,
            text="⚡ PULSE",
            font=(AppStyles.FONT, 20, "bold"),
            text_color=AppStyles.ACCENT
        ).pack(side="left")
        ctk.CTkLabel(
            brand_wrap,
            text="STUDIO",
            font=(AppStyles.FONT, 20, "bold"),
            text_color=AppStyles.TEXT_WHITE
        ).pack(side="left", padx=4)

        self.nav_btns = {}
        routes = [
            ("EXPLORE", "Explore & Search", "🌐"),
            ("FAVORITES", "Favorites", "♥"),
            ("LIBRARY", "Saved Collection", "🗂"),
            ("HISTORY", "Listening Log", "🕒")
        ]
        for key, name, icon in routes:
            btn = SidebarNavButton(self.sidebar, name, icon, command=lambda k=key: self.navigate(k))
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_btns[key] = btn

        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=AppStyles.BORDER_SUBTLE)
        sep.pack(fill="x", padx=12, pady=12)

        pl_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        pl_header.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(
            pl_header,
            text="PLAYLISTS",
            font=(AppStyles.FONT, 10, "bold"),
            text_color=AppStyles.TEXT_MUTED
        ).pack(side="left")

        ctk.CTkButton(
            pl_header,
            text="＋",
            width=24,
            height=24,
            corner_radius=12,
            fg_color="transparent",
            hover_color=AppStyles.BG_CARD_HOVER,
            text_color=AppStyles.ACCENT,
            font=(AppStyles.FONT, 14, "bold"),
            command=self.create_playlist_dialog
        ).pack(side="right")

        self.playlist_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.playlist_container.pack(fill="x", padx=4, pady=(0, 4))

        sep2 = ctk.CTkFrame(self.sidebar, height=1, fg_color=AppStyles.BORDER_SUBTLE)
        sep2.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            self.sidebar,
            text="STUDIO SUITE",
            font=(AppStyles.FONT, 10, "bold"),
            text_color=AppStyles.TEXT_MUTED
        ).pack(anchor="w", padx=16, pady=(0, 4))

        SidebarNavButton(self.sidebar, "AI Shazam Match", "🎙", self.identify_song_workflow).pack(fill="x", padx=8, pady=2)
        SidebarNavButton(self.sidebar, "Import Audio File", "📂", self.import_local_tracks).pack(fill="x", padx=8, pady=2)
        SidebarNavButton(self.sidebar, "Toggle Right Stage", "◨", self.toggle_drawer).pack(fill="x", padx=8, pady=2)

        self.center_stage = ctk.CTkFrame(self, fg_color=AppStyles.BG_BASE, corner_radius=0)
        self.center_stage.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.search_bar = ModernSearchArea(self.center_stage, self.handle_query_search)
        self.search_bar.pack(fill="x", pady=(0, 16))

        self.hero = HeroBanner(self.center_stage, play_callback=self.request_playback)
        self.hero.pack(fill="x", pady=(0, 16))

        table_header = ctk.CTkFrame(self.center_stage, fg_color="transparent", height=28)
        table_header.pack(fill="x", padx=8, pady=(0, 6))
        ctk.CTkLabel(table_header, text="#", width=36, font=(AppStyles.FONT, 11, "bold"),
                     text_color=AppStyles.TEXT_MUTED).pack(side="left", padx=(10, 4))
        ctk.CTkLabel(table_header, text="TITLE & ARTIST", font=(AppStyles.FONT, 11, "bold"),
                     text_color=AppStyles.TEXT_MUTED).pack(side="left", padx=58)
        ctk.CTkLabel(table_header, text="SOURCE", font=(AppStyles.FONT, 11, "bold"),
                     text_color=AppStyles.TEXT_MUTED).pack(side="right", padx=18)
        ctk.CTkLabel(table_header, text="TIME", font=(AppStyles.FONT, 11, "bold"),
                     text_color=AppStyles.TEXT_MUTED).pack(side="right", padx=22)

        self.track_scroll = ctk.CTkScrollableFrame(self.center_stage, fg_color="transparent")
        self.track_scroll.pack(fill="both", expand=True)

        self.drawer = ctk.CTkFrame(
            self,
            fg_color=AppStyles.BG_DRAWER,
            corner_radius=0,
            border_width=1,
            border_color=AppStyles.BORDER_SUBTLE
        )
        self.drawer.grid(row=0, column=2, sticky="nsew")
        self.setup_drawer_content()

        self.setup_bottom_player()

    def setup_drawer_content(self):
        d_head = ctk.CTkFrame(self.drawer, fg_color="transparent")
        d_head.pack(fill="x", padx=20, pady=(24, 12))
        ctk.CTkLabel(d_head, text="NOW PLAYING", font=(AppStyles.FONT, 13, "bold"),
                     text_color=AppStyles.TEXT_WHITE).pack(side="left")

        self.drawer_art_box = ctk.CTkLabel(
            self.drawer,
            text="",
            image=create_rounded_cover("", size=(260, 260), radius=16),
            width=260,
            height=260
        )
        self.drawer_art_box.pack(padx=20, pady=10)

        self.drawer_title = ctk.CTkLabel(
            self.drawer,
            text="Pulse Stream Standby",
            font=(AppStyles.FONT, 16, "bold"),
            text_color=AppStyles.TEXT_WHITE,
            wraplength=270
        )
        self.drawer_title.pack(padx=20, pady=(10, 2))

        self.drawer_artist = ctk.CTkLabel(
            self.drawer,
            text="Ready to Play",
            font=(AppStyles.FONT, 12),
            text_color=AppStyles.TEXT_MUTED
        )
        self.drawer_artist.pack(padx=20, pady=(0, 14))

        lyrics_title_bar = ctk.CTkFrame(self.drawer, fg_color="transparent")
        lyrics_title_bar.pack(fill="x", padx=20, pady=(10, 4))
        ctk.CTkLabel(lyrics_title_bar, text="LIVE LYRICS", font=(AppStyles.FONT, 11, "bold"),
                     text_color=AppStyles.ACCENT).pack(side="left")

        self.lyrics_scroll = ctk.CTkScrollableFrame(self.drawer, fg_color="transparent")
        self.lyrics_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.lyric_widgets = []

    def setup_bottom_player(self):
        self.dock = ctk.CTkFrame(
            self,
            height=92,
            fg_color=AppStyles.BG_PLAYER,
            corner_radius=0,
            border_width=1,
            border_color=AppStyles.BORDER_SUBTLE
        )
        self.dock.grid(row=1, column=0, columnspan=3, sticky="nsew")
        self.dock.pack_propagate(False)

        left_pane = ctk.CTkFrame(self.dock, fg_color="transparent", width=320)
        left_pane.pack(side="left", fill="y", padx=(18, 0))
        left_pane.pack_propagate(False)

        self.dock_art = ctk.CTkLabel(
            left_pane,
            text="",
            image=create_rounded_cover("", size=(52, 52), radius=10),
            width=52,
            height=52
        )
        self.dock_art.pack(side="left", pady=20)

        meta_box = ctk.CTkFrame(left_pane, fg_color="transparent")
        meta_box.pack(side="left", fill="both", expand=True, padx=(12, 6), pady=22)

        self.dock_title_lbl = ctk.CTkLabel(
            meta_box,
            text="PulseStream Ready",
            font=(AppStyles.FONT, 13, "bold"),
            text_color=AppStyles.TEXT_WHITE,
            anchor="w"
        )
        self.dock_title_lbl.pack(fill="x")

        self.dock_sub_lbl = ctk.CTkLabel(
            meta_box,
            text="Select track to listen",
            font=(AppStyles.FONT, 11),
            text_color=AppStyles.TEXT_MUTED,
            anchor="w"
        )
        self.dock_sub_lbl.pack(fill="x")

        self.dock_fav_btn = ctk.CTkButton(
            left_pane,
            text="♡",
            width=32,
            height=32,
            corner_radius=16,
            fg_color="transparent",
            hover_color=AppStyles.BG_CARD_HOVER,
            text_color=AppStyles.TEXT_MUTED,
            font=(AppStyles.FONT, 16),
            command=self._on_dock_fav_toggle
        )
        self.dock_fav_btn.pack(side="left", padx=4)

        right_pane = ctk.CTkFrame(self.dock, fg_color="transparent", width=300)
        right_pane.pack(side="right", fill="y", padx=(0, 20))
        right_pane.pack_propagate(False)

        self.visualizer = AnimatedVisualizer(right_pane, width=76, height=24, bar_count=6)
        self.visualizer.pack(side="left", padx=(8, 14), pady=34)

        ctk.CTkButton(
            right_pane,
            text="◨",
            width=30,
            height=30,
            corner_radius=15,
            fg_color="transparent",
            hover_color=AppStyles.BG_CARD_HOVER,
            text_color=AppStyles.TEXT_MED,
            font=(AppStyles.FONT, 14),
            command=self.toggle_drawer
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            right_pane,
            text="🔊",
            font=(AppStyles.FONT, 12),
            text_color=AppStyles.TEXT_MUTED
        ).pack(side="left", padx=(10, 4))

        self.vol_slider = ctk.CTkSlider(
            right_pane,
            width=92,
            height=6,
            progress_color=AppStyles.ACCENT,
            fg_color="#272733",
            button_color=AppStyles.TEXT_WHITE,
            button_hover_color=AppStyles.ACCENT,
            button_length=10,
            button_corner_radius=5,
            command=self.player.set_volume
        )
        self.vol_slider.pack(side="left", padx=4)
        self.vol_slider.set(0.8)

        center_pane = ctk.CTkFrame(self.dock, fg_color="transparent")
        center_pane.pack(side="left", fill="both", expand=True, padx=16)

        button_row = ctk.CTkFrame(center_pane, fg_color="transparent")
        button_row.pack(side="top", pady=(12, 2))

        self.shuf_btn = ctk.CTkButton(
            button_row,
            text="🔀",
            width=32,
            height=32,
            corner_radius=16,
            fg_color="transparent",
            hover_color=AppStyles.BG_CARD_HOVER,
            text_color=AppStyles.TEXT_MUTED,
            font=(AppStyles.FONT, 13),
            command=self.toggle_shuffle
        )
        self.shuf_btn.pack(side="left", padx=6)

        ctk.CTkButton(
            button_row,
            text="⏮",
            width=36,
            height=36,
            corner_radius=18,
            fg_color="transparent",
            hover_color=AppStyles.BG_CARD_HOVER,
            text_color=AppStyles.TEXT_WHITE,
            font=(AppStyles.FONT, 16),
            command=self.prev_track
        ).pack(side="left", padx=4)

        self.main_play_btn = ctk.CTkButton(
            button_row,
            text="▶",
            width=40,
            height=40,
            corner_radius=20,
            fg_color=AppStyles.TEXT_WHITE,
            text_color="#000000",
            hover_color=AppStyles.ACCENT,
            font=(AppStyles.FONT, 15, "bold"),
            command=self.toggle_play_state
        )
        self.main_play_btn.pack(side="left", padx=10)

        ctk.CTkButton(
            button_row,
            text="⏭",
            width=36,
            height=36,
            corner_radius=18,
            fg_color="transparent",
            hover_color=AppStyles.BG_CARD_HOVER,
            text_color=AppStyles.TEXT_WHITE,
            font=(AppStyles.FONT, 16),
            command=self.next_track
        ).pack(side="left", padx=4)

        self.rep_btn = ctk.CTkButton(
            button_row,
            text="🔁",
            width=32,
            height=32,
            corner_radius=16,
            fg_color="transparent",
            hover_color=AppStyles.BG_CARD_HOVER,
            text_color=AppStyles.TEXT_MUTED,
            font=(AppStyles.FONT, 13),
            command=self.toggle_repeat
        )
        self.rep_btn.pack(side="left", padx=6)

        timeline_row = ctk.CTkFrame(center_pane, fg_color="transparent")
        timeline_row.pack(side="top", fill="x", padx=20, pady=(2, 6))

        self.elapsed_lbl = ctk.CTkLabel(
            timeline_row,
            text="00:00",
            font=(AppStyles.FONT, 11),
            text_color=AppStyles.TEXT_MUTED,
            width=36
        )
        self.elapsed_lbl.pack(side="left", padx=(0, 8))

        self.seek_bar = ctk.CTkSlider(
            timeline_row,
            from_=0,
            to=100,
            height=5,
            progress_color=AppStyles.ACCENT,
            fg_color="#262633",
            button_color=AppStyles.TEXT_WHITE,
            button_hover_color=AppStyles.ACCENT,
            button_length=10,
            button_corner_radius=5,
            command=self._on_slider_move
        )
        self.seek_bar.pack(side="left", fill="x", expand=True)
        self.seek_bar.set(0)
        self.seek_bar.bind("<Button-1>", lambda e: setattr(self, "is_seeking", True))
        self.seek_bar.bind("<ButtonRelease-1>", self._on_slider_release)

        self.duration_lbl = ctk.CTkLabel(
            timeline_row,
            text="00:00",
            font=(AppStyles.FONT, 11),
            text_color=AppStyles.TEXT_MUTED,
            width=36
        )
        self.duration_lbl.pack(side="left", padx=(8, 0))

    def refresh_sidebar_playlists(self):
        for w in self.playlist_container.winfo_children():
            w.destroy()
        playlists = self.db.get_playlists()
        for pl in playlists:
            pid = pl["id"]
            pname = pl["name"]
            is_act = self.current_tab == f"PLAYLIST_{pid}"
            btn = SidebarNavButton(
                self.playlist_container,
                pname[:18],
                "🎵",
                command=lambda p=pid: self.navigate(f"PLAYLIST_{p}"),
                is_active=is_act
            )
            btn.pack(fill="x", padx=4, pady=1)

    def create_playlist_dialog(self):
        dialog = ctk.CTkInputDialog(text="Enter playlist title:", title="New Playlist")
        name = dialog.get_input()
        if name and name.strip():
            pid = self.db.create_playlist(name.strip())
            if pid:
                self.refresh_sidebar_playlists()
                self.navigate(f"PLAYLIST_{pid}")
            else:
                messagebox.showwarning("Playlists", "A playlist with this name already exists.")

    def prompt_add_to_playlist(self, track_data):
        playlists = self.db.get_playlists()
        if not playlists:
            if messagebox.askyesno("No Playlists", "You have not created any playlists yet. Would you like to create one now?"):
                self.create_playlist_dialog()
            return

        picker = ctk.CTkToplevel(self)
        picker.title("Add to Playlist")
        picker.geometry("380x440")
        picker.configure(fg_color=AppStyles.BG_SURFACE)
        picker.transient(self)
        picker.grab_set()

        ctk.CTkLabel(
            picker,
            text="Add to Playlist",
            font=(AppStyles.FONT, 16, "bold"),
            text_color=AppStyles.TEXT_WHITE
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            picker,
            text=f"Song: {track_data.get('title', 'Unknown')[:35]}",
            font=(AppStyles.FONT, 12),
            text_color=AppStyles.TEXT_MUTED
        ).pack(pady=(0, 14))

        scroll = ctk.CTkScrollableFrame(picker, fg_color=AppStyles.BG_BASE, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        for pl in playlists:
            pid = pl["id"]
            pname = pl["name"]
            p_btn = ctk.CTkButton(
                scroll,
                text=f"  🎵   {pname}",
                anchor="w",
                fg_color=AppStyles.BG_CARD,
                hover_color=AppStyles.BG_CARD_HOVER,
                text_color=AppStyles.TEXT_WHITE,
                font=(AppStyles.FONT, 13),
                height=38,
                corner_radius=8,
                command=lambda target_pid=pid, win=picker: self._execute_add_to_playlist(target_pid, track_data, win)
            )
            p_btn.pack(fill="x", pady=3)

    def _execute_add_to_playlist(self, playlist_id, track_data, picker_window):
        ok = self.db.add_track_to_playlist(playlist_id, track_data)
        picker_window.destroy()
        if ok:
            messagebox.showinfo("Playlist", "Track added successfully.")
            if self.current_tab == f"PLAYLIST_{playlist_id}":
                self.navigate(self.current_tab)
        else:
            messagebox.showinfo("Playlist", "Track is already in this playlist.")

    def _on_dock_fav_toggle(self):
        if not self.current_track:
            return
        is_now_fav = self.toggle_favorite(self.current_track)
        self.dock_fav_btn.configure(
            text="♥" if is_now_fav else "♡",
            text_color=AppStyles.DANGER if is_now_fav else AppStyles.TEXT_MUTED
        )

    def toggle_drawer(self):
        if self.is_drawer_visible:
            self.drawer.grid_remove()
            self.grid_columnconfigure(2, weight=0, minsize=0)
            self.is_drawer_visible = False
        else:
            self.drawer.grid()
            self.grid_columnconfigure(2, weight=0, minsize=320)
            self.is_drawer_visible = True

    def navigate(self, tab):
        self.current_tab = tab
        for key, btn in self.nav_btns.items():
            btn.configure(
                fg_color=AppStyles.BG_CARD if key == tab else "transparent",
                text_color=AppStyles.TEXT_WHITE if key == tab else AppStyles.TEXT_MED,
                border_width=1 if key == tab else 0
            )

        self.refresh_sidebar_playlists()

        if tab == "EXPLORE":
            self.render_explore()
        elif tab == "FAVORITES":
            self.render_list(self.db.get_favorites(), "Your Favorite Tracks")
        elif tab == "LIBRARY":
            self.render_list(self.db.get_all_saved(), "Saved Offline Collection")
        elif tab == "HISTORY":
            self.render_list(self.db.get_history(), "Recent Playback Log")
        elif tab.startswith("PLAYLIST_"):
            pid = int(tab.split("_")[1])
            self.render_playlist_view(pid)

    def render_playlist_view(self, playlist_id):
        for w in self.track_scroll.winfo_children():
            w.destroy()

        pl_info = self.db.get_playlist_by_id(playlist_id)
        if not pl_info:
            self.navigate("EXPLORE")
            return

        tracks = self.db.get_playlist_tracks(playlist_id)

        header_box = ctk.CTkFrame(self.track_scroll, fg_color="transparent")
        header_box.pack(fill="x", pady=(0, 10))

        title_area = ctk.CTkFrame(header_box, fg_color="transparent")
        title_area.pack(side="left")

        ctk.CTkLabel(
            title_area,
            text=f"PLAYLIST: {pl_info['name']}",
            font=(AppStyles.FONT, 18, "bold"),
            text_color=AppStyles.TEXT_WHITE
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_area,
            text=f"{len(tracks)} songs in collection",
            font=(AppStyles.FONT, 12),
            text_color=AppStyles.TEXT_MUTED
        ).pack(anchor="w")

        ctk.CTkButton(
            header_box,
            text="🗑 Delete Playlist",
            width=120,
            height=30,
            corner_radius=8,
            fg_color=AppStyles.BG_CARD,
            hover_color=AppStyles.DANGER,
            text_color=AppStyles.TEXT_WHITE,
            font=(AppStyles.FONT, 12),
            command=lambda: self.confirm_delete_playlist(playlist_id, pl_info["name"])
        ).pack(side="right")

        if tracks:
            self.hero.update_hero(tracks[0])
            for idx, item in enumerate(tracks, start=1):
                self.create_row(idx, item)
        else:
            ctk.CTkLabel(
                self.track_scroll,
                text="This playlist is empty. Right-click any song and select 'Add to Playlist...' to add tracks.",
                font=(AppStyles.FONT, 13),
                text_color=AppStyles.TEXT_MUTED
            ).pack(pady=50)

    def confirm_delete_playlist(self, playlist_id, name):
        if messagebox.askyesno("Delete Playlist", f"Are you sure you want to delete '{name}'?"):
            self.db.delete_playlist(playlist_id)
            self.refresh_sidebar_playlists()
            self.navigate("EXPLORE")

    def render_explore(self):
        for w in self.track_scroll.winfo_children():
            w.destroy()
        items = self.db.get_all_saved()
        if items:
            self.hero.update_hero(items[0])
            for idx, item in enumerate(items, start=1):
                self.create_row(idx, item)
        else:
            ctk.CTkLabel(
                self.track_scroll,
                text="Search any song, artist or album above to begin lossless streaming.",
                font=(AppStyles.FONT, 14),
                text_color=AppStyles.TEXT_MUTED
            ).pack(pady=60)

    def render_list(self, items, title):
        for w in self.track_scroll.winfo_children():
            w.destroy()
        if not items:
            ctk.CTkLabel(
                self.track_scroll,
                text=f"{title} is currently empty.",
                font=(AppStyles.FONT, 14),
                text_color=AppStyles.TEXT_MUTED
            ).pack(pady=60)
            return
        self.hero.update_hero(items[0])
        for idx, item in enumerate(items, start=1):
            self.create_row(idx, item)

    def create_row(self, idx, data):
        identifier = data.get("path") or data.get("url", "")
        is_fav = self.db.is_favorite(identifier)
        row = TrackTableRow(
            self.track_scroll,
            idx=idx,
            data=data,
            play_cmd=self.request_playback,
            fav_cmd=self.toggle_favorite,
            save_cmd=self.save_track_offline,
            del_cmd=self.delete_track,
            is_fav=is_fav
        )
        row.pack(fill="x", pady=2)

    def handle_query_search(self):
        query = self.search_bar.get()
        if not query:
            return
        is_url = str(query).startswith("http://") or str(query).startswith("https://")

        if is_url:
            cached_instant = self.searcher.get_cached_path({"url": query})
            if cached_instant and os.path.exists(cached_instant) and os.path.getsize(cached_instant) > 50000:
                fast_track = {
                    "title": os.path.splitext(os.path.basename(cached_instant))[0],
                    "artist": "Cached Stream",
                    "path": cached_instant,
                    "url": query,
                    "source": "STREAM"
                }
                self.request_playback(fast_track)
                return

        self.search_bar.set_state("disabled")
        for w in self.track_scroll.winfo_children():
            w.destroy()

        loading = ctk.CTkLabel(
            self.track_scroll,
            text=f"Connecting to global stream relays for '{query}'...",
            font=(AppStyles.FONT, 14),
            text_color=AppStyles.TEXT_MUTED
        )
        loading.pack(pady=40)

        def worker():
            results = self.searcher.search_tracks(query, limit=8)
            def update():
                self.search_bar.set_state("normal")
                for w in self.track_scroll.winfo_children():
                    w.destroy()
                if not results:
                    ctk.CTkLabel(
                        self.track_scroll,
                        text="No audio matches found. Please refine your query.",
                        font=(AppStyles.FONT, 14),
                        text_color=AppStyles.TEXT_MUTED
                    ).pack(pady=40)
                    return
                self.hero.update_hero(results[0])
                for idx, r in enumerate(results, start=1):
                    self.create_row(idx, r)

                if is_url and results:
                    self.request_playback(results[0])

            self.after(0, update)
        threading.Thread(target=worker, daemon=True).start()

    def request_playback(self, track_data):
        if not track_data:
            return

        cached_hit = self.searcher.get_cached_path(track_data)
        if cached_hit and os.path.exists(cached_hit) and os.path.getsize(cached_hit) > 50000:
            track_data["path"] = cached_hit
            self._execute_play(track_data)
            return

        self.dock_title_lbl.configure(text=f"Buffering: {track_data.get('title', 'Track')[:22]}...")
        def dl_worker():
            try:
                def on_prog(txt):
                    self.after(0, lambda: self.dock_title_lbl.configure(text=txt))

                resolved = self.searcher.download_track(track_data, on_progress=on_prog)
                track_data["path"] = resolved["path"]
                track_data["url"] = resolved.get("url", track_data.get("url", ""))
                track_data["thumbnail"] = resolved["thumbnail"]
                self.after(0, lambda: self._execute_play(resolved))
            except Exception as ex:
                raw_msg = str(ex)
                clean_msg = re.sub(r'\x1b\[[0-9;]*m', '', raw_msg).strip()
                if not clean_msg:
                    clean_msg = "Stream extraction failed. Please check internet connection."
                self.after(0, lambda: messagebox.showerror("Stream Error", clean_msg))
        threading.Thread(target=dl_worker, daemon=True).start()

    def _execute_play(self, track_data):
        if not track_data or not isinstance(track_data, dict):
            messagebox.showerror("Error", "Invalid track stream payload.")
            return

        fp = track_data.get("path")
        if not fp or not os.path.exists(fp):
            messagebox.showerror("Error", "Audio track could not be resolved on storage.")
            return

        dur = track_data.get("duration", 0)
        if dur <= 0:
            try:
                audio = MP3(fp)
                dur = audio.info.length
            except Exception:
                dur = 240

        track_data["duration"] = dur
        self.current_track = track_data
        self.current_duration = dur

        self.db.add_or_update_track(
            title=track_data.get("title", "Unknown"),
            artist=track_data.get("artist", "Unknown"),
            duration=dur,
            path=fp,
            thumbnail=track_data.get("thumbnail", ""),
            source=track_data.get("source", "LOCAL"),
            url=track_data.get("url", "")
        )
        self.db.record_play(fp)

        ok = self.player.play(fp)
        if ok:
            self.main_play_btn.configure(text="⏸")
            self.seek_bar.configure(to=dur)
            self.seek_bar.set(0)
            self.elapsed_lbl.configure(text="00:00")
            self.duration_lbl.configure(text=format_time(dur))
            self.visualizer.set_playing(True)

            self.dock_title_lbl.configure(text=track_data.get("title", "Unknown")[:26])
            self.dock_sub_lbl.configure(text=track_data.get("artist", "Unknown")[:24])
            cover_img = create_rounded_cover(track_data.get("thumbnail", ""), size=(52, 52), radius=10)
            self.dock_art.configure(image=cover_img)

            is_fav = self.db.is_favorite(fp)
            self.dock_fav_btn.configure(
                text="♥" if is_fav else "♡",
                text_color=AppStyles.DANGER if is_fav else AppStyles.TEXT_MUTED
            )

            self.drawer_title.configure(text=track_data.get("title", "Unknown")[:30])
            self.drawer_artist.configure(text=track_data.get("artist", "Unknown")[:26])
            drawer_img = create_rounded_cover(track_data.get("thumbnail", ""), size=(260, 260), radius=16)
            self.drawer_art_box.configure(image=drawer_img)

            self.hero.update_hero(track_data)
            self.load_lyrics_for_current()
            if track_data not in self.queue:
                self.queue.append(track_data)
        else:
            messagebox.showerror("Error", "Playback failed on current track.")

    def toggle_play_state(self):
        if not self.current_track and self.queue:
            self.request_playback(self.queue[0])
            return
        if self.player.is_active():
            paused = self.player.toggle_pause()
            self.main_play_btn.configure(text="▶" if paused else "⏸")
            self.visualizer.set_playing(not paused)

    def prev_track(self):
        if not self.queue:
            return
        if self.player.get_pos() > 3:
            self.player.seek(0)
            return
        try:
            curr = self.queue.index(self.current_track)
            idx = curr - 1 if curr > 0 else len(self.queue) - 1
            self.request_playback(self.queue[idx])
        except Exception:
            self.request_playback(self.queue[0])

    def next_track(self):
        if not self.queue:
            return
        if self.repeat_mode == "ONE":
            self.player.seek(0)
            return
        if self.shuffle_mode:
            self.request_playback(random.choice(self.queue))
            return
        try:
            curr = self.queue.index(self.current_track)
            nxt = curr + 1
            if nxt < len(self.queue):
                self.request_playback(self.queue[nxt])
            elif self.repeat_mode == "ALL":
                self.request_playback(self.queue[0])
        except Exception:
            self.request_playback(self.queue[0])

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        self.shuf_btn.configure(text_color=AppStyles.ACCENT if self.shuffle_mode else AppStyles.TEXT_MUTED)

    def toggle_repeat(self):
        if self.repeat_mode == "NONE":
            self.repeat_mode = "ALL"
            self.rep_btn.configure(text="🔁", text_color=AppStyles.ACCENT)
        elif self.repeat_mode == "ALL":
            self.repeat_mode = "ONE"
            self.rep_btn.configure(text="🔂", text_color=AppStyles.SECONDARY)
        else:
            self.repeat_mode = "NONE"
            self.rep_btn.configure(text="🔁", text_color=AppStyles.TEXT_MUTED)

    def _on_slider_move(self, val):
        pass

    def _on_slider_release(self, evt):
        self.is_seeking = False
        target = self.seek_bar.get()
        self.player.seek(target)

    def toggle_favorite(self, track_data):
        if not track_data:
            return False
        return self.db.toggle_favorite_track(track_data)

    def add_to_queue(self, track_data):
        self.queue.append(track_data)
        messagebox.showinfo("Queue", f"Track '{track_data.get('title', 'Track')[:25]}' enqueued.")

    def delete_track(self, track_data):
        if self.current_tab.startswith("PLAYLIST_"):
            pid = int(self.current_tab.split("_")[1])
            tid = track_data.get("id")
            if tid:
                self.db.remove_track_from_playlist(pid, tid)
            self.navigate(self.current_tab)
            return

        if track_data == self.current_track:
            self.player.stop()
            self.visualizer.set_playing(False)
            self.dock_title_lbl.configure(text="PulseStream Ready")
            self.dock_sub_lbl.configure(text="")
        if track_data in self.queue:
            self.queue.remove(track_data)
        self.navigate(self.current_tab)

    def save_track_offline(self, track_data):
        src = track_data.get("path")
        if not src or not os.path.exists(src):
            messagebox.showwarning("PulseStream", "Audio must be fully buffered before saving.")
            return
        ext = os.path.splitext(src)[1] or ".mp3"
        safe = sanitize_filename(track_data.get("title", "track"))
        dest = filedialog.asksaveasfilename(defaultextension=ext, initialfile=f"{safe}{ext}")
        if dest:
            shutil.copyfile(src, dest)
            messagebox.showinfo("Exported", "Track stored to permanent media storage.")

    def import_local_tracks(self):
        files = filedialog.askopenfilenames(
            title="Import Audio Files",
            filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.m4a *.ogg")]
        )
        for f in files:
            name = os.path.splitext(os.path.basename(f))[0]
            dur = 0
            try:
                dur = MP3(f).info.length
            except Exception:
                pass
            self.db.add_or_update_track(title=name, artist="Local Artist", duration=dur, path=f, source="LOCAL")
        if files:
            self.navigate("LIBRARY")

    def identify_song_workflow(self):
        messagebox.showinfo("Pulse AI", "Listening to ambient acoustics for 7 seconds...")
        def task():
            tmp = "cache/ai_sample.wav"
            try:
                self.recorder.record(tmp, seconds=7)
                res = asyncio.run(self.recognizer.identify(tmp))
                if "track" in res:
                    t = res["track"]["title"]
                    a = res["track"]["subtitle"]
                    q = f"{t} {a}"
                    def confirm():
                        if messagebox.askyesno("Match Found", f"Song: {t}\nArtist: {a}\n\nStream now?"):
                            self.navigate("EXPLORE")
                            self.search_bar.set_text(q)
                            self.handle_query_search()
                    self.after(0, confirm)
                else:
                    self.after(0, lambda: messagebox.showwarning("Shazam", "No acoustic match recognized."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("AI Error", str(e)))
            finally:
                if os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except Exception:
                        pass
        threading.Thread(target=task, daemon=True).start()

    def load_lyrics_for_current(self):
        if not self.current_track:
            return
        t = self.current_track.get("title", "")
        a = self.current_track.get("artist", "")
        d = self.current_track.get("duration", 0)
        def worker():
            res = self.lyrics_service.fetch_lyrics(t, a, d)
            self.lyrics_data = res
            self.after(0, self.render_lyrics_teleprompter)
        threading.Thread(target=worker, daemon=True).start()

    def render_lyrics_teleprompter(self):
        for w in self.lyrics_scroll.winfo_children():
            w.destroy()
        self.lyric_widgets.clear()
        self.active_lyric_index = -1

        if self.lyrics_data["type"] == "synced":
            for ts, line in self.lyrics_data["lines"]:
                lbl = ctk.CTkLabel(
                    self.lyrics_scroll,
                    text=line if line else "•••",
                    font=(AppStyles.FONT, 13, "bold"),
                    text_color=AppStyles.TEXT_MUTED,
                    anchor="w",
                    wraplength=260
                )
                lbl.pack(fill="x", pady=6)
                self.lyric_widgets.append((ts, lbl))
        elif self.lyrics_data["type"] == "plain":
            for line in self.lyrics_data.get("text", "").splitlines():
                ctk.CTkLabel(
                    self.lyrics_scroll,
                    text=line if line else " ",
                    font=(AppStyles.FONT, 12),
                    text_color=AppStyles.TEXT_MED,
                    anchor="w",
                    wraplength=260
                ).pack(fill="x", pady=2)
        else:
            ctk.CTkLabel(
                self.lyrics_scroll,
                text="No lyrics synced for this title.",
                font=(AppStyles.FONT, 12),
                text_color=AppStyles.TEXT_MUTED
            ).pack(pady=40)

    def sync_live_lyrics(self, cur_pos):
        if self.lyrics_data["type"] != "synced" or not self.lyric_widgets:
            return
        target = -1
        for i, (ts, _) in enumerate(self.lyric_widgets):
            if cur_pos >= ts:
                target = i
            else:
                break
        if target != self.active_lyric_index and target != -1:
            if self.active_lyric_index != -1 and self.active_lyric_index < len(self.lyric_widgets):
                self.lyric_widgets[self.active_lyric_index][1].configure(
                    text_color=AppStyles.TEXT_MUTED,
                    font=(AppStyles.FONT, 13, "bold")
                )
            self.lyric_widgets[target][1].configure(
                text_color=AppStyles.ACCENT,
                font=(AppStyles.FONT, 15, "bold")
            )
            self.active_lyric_index = target

    def start_main_clock(self):
        if self.player.is_active() and not self.is_seeking:
            pos = self.player.get_pos()
            self.seek_bar.set(pos)
            self.elapsed_lbl.configure(text=format_time(pos))
            self.duration_lbl.configure(text=format_time(self.current_duration))
            self.visualizer.update_bars()
            self.sync_live_lyrics(pos)

            if pos >= self.current_duration and self.current_duration > 0:
                self.next_track()

        self.after(200, self.start_main_clock)

if __name__ == "__main__":
    app = PulseStreamStudio()
    app.mainloop()