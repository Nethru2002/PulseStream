import os
import random
import threading
import requests
import customtkinter as ctk
from tkinter import Canvas, Menu
from PIL import Image, ImageDraw, ImageOps
from ui.styles import AppStyles
from utils.helpers import format_time

def create_rounded_cover(image_path_or_obj, size=(50, 50), radius=10):
    try:
        if isinstance(image_path_or_obj, str):
            p = image_path_or_obj.strip()
            if not p or not os.path.exists(p):
                img = Image.new("RGBA", size, color="#1A1D2B")
            else:
                img = Image.open(p).convert("RGBA")
        elif image_path_or_obj is None:
            img = Image.new("RGBA", size, color="#1A1D2B")
        else:
            img = image_path_or_obj.convert("RGBA")

        img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
        rounded = Image.new("RGBA", size, (0, 0, 0, 0))
        rounded.paste(img, (0, 0), mask=mask)
        return ctk.CTkImage(light_image=rounded, dark_image=rounded, size=size)
    except Exception:
        fallback = Image.new("RGBA", size, color="#1A1D2B")
        return ctk.CTkImage(light_image=fallback, dark_image=fallback, size=size)

class AnimatedVisualizer(Canvas):
    def __init__(self, master, width=80, height=24, bar_count=7, **kwargs):
        super().__init__(
            master,
            width=width,
            height=height,
            bg=AppStyles.BG_DECK,
            highlightthickness=0,
            **kwargs
        )
        self.width = width
        self.height = height
        self.bar_count = bar_count
        self.is_active = False
        self.bars = []
        bar_width = (width - ((bar_count - 1) * 2)) / bar_count
        for i in range(bar_count):
            x1 = i * (bar_width + 2)
            x2 = x1 + bar_width
            rect = self.create_rectangle(x1, height - 3, x2, height, fill=AppStyles.ACCENT, width=0)
            self.bars.append((rect, x1, x2))

    def set_playing(self, is_playing):
        self.is_active = is_playing
        if not is_playing:
            self._reset_bars()

    def update_bars(self):
        if not self.is_active:
            return
        for rect, x1, x2 in self.bars:
            h = random.randint(3, self.height)
            self.coords(rect, x1, self.height - h, x2, self.height)

    def _reset_bars(self):
        for rect, x1, x2 in self.bars:
            self.coords(rect, x1, self.height - 3, x2, self.height)

class HeroShowcase(ctk.CTkFrame):
    def __init__(self, master, play_callback, fav_callback, **kwargs):
        super().__init__(
            master,
            fg_color=AppStyles.BG_SURFACE,
            corner_radius=20,
            border_width=1,
            border_color=AppStyles.BORDER_CARD,
            height=200,
            **kwargs
        )
        self.pack_propagate(False)
        self.play_callback = play_callback
        self.fav_callback = fav_callback
        self.current_data = None

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=18)

        self.cover_lbl = ctk.CTkLabel(
            inner,
            text="",
            image=create_rounded_cover("", size=(140, 140), radius=16),
            width=140,
            height=140
        )
        self.cover_lbl.pack(side="left", padx=(0, 24))

        meta = ctk.CTkFrame(inner, fg_color="transparent")
        meta.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            meta,
            text="FEATURED TRACK",
            font=(AppStyles.FONT, 10, "bold"),
            text_color=AppStyles.ACCENT
        ).pack(anchor="w")

        self.title_lbl = ctk.CTkLabel(
            meta,
            text="Welcome to PulseStream",
            font=(AppStyles.FONT, 18, "bold"),
            text_color=AppStyles.TEXT_TITLE,
            anchor="w",
            wraplength=580,
            justify="left"
        )
        self.title_lbl.pack(anchor="w", pady=(4, 2), fill="x")

        self.artist_lbl = ctk.CTkLabel(
            meta,
            text="Discover, stream and build your offline music collection",
            font=(AppStyles.FONT, 13),
            text_color=AppStyles.TEXT_MUTED,
            anchor="w",
            wraplength=580,
            justify="left"
        )
        self.artist_lbl.pack(anchor="w", pady=(0, 14), fill="x")

        action_row = ctk.CTkFrame(meta, fg_color="transparent")
        action_row.pack(anchor="w")

        self.play_btn = ctk.CTkButton(
            action_row,
            text="▶  Play Now",
            width=130,
            height=36,
            corner_radius=18,
            fg_color=AppStyles.ACCENT,
            text_color=AppStyles.TEXT_WHITE,
            hover_color=AppStyles.ACCENT_HOVER,
            font=(AppStyles.FONT, 12, "bold"),
            command=self._on_play
        )
        self.play_btn.pack(side="left", padx=(0, 10))

        self.fav_btn = ctk.CTkButton(
            action_row,
            text="♡  Favorite",
            width=110,
            height=36,
            corner_radius=18,
            fg_color=AppStyles.BG_CARD,
            hover_color=AppStyles.BG_CARD_HOVER,
            text_color=AppStyles.TEXT_WHITE,
            font=(AppStyles.FONT, 12, "bold"),
            command=self._on_fav
        )
        self.fav_btn.pack(side="left")

    def update_hero(self, track_data, is_fav=False):
        self.current_data = track_data
        self.title_lbl.configure(text=track_data.get("title", ""))
        self.artist_lbl.configure(text=track_data.get("artist", "Unknown Artist"))

        thumb_src = track_data.get("thumbnail", "")
        self._resolve_and_set_thumb(thumb_src)

        self.fav_btn.configure(
            text="♥  Liked" if is_fav else "♡  Favorite",
            text_color=AppStyles.ACCENT if is_fav else AppStyles.TEXT_WHITE
        )

    def _resolve_and_set_thumb(self, thumb_src):
        if thumb_src and os.path.exists(thumb_src):
            img = create_rounded_cover(thumb_src, size=(140, 140), radius=16)
            self.cover_lbl.configure(image=img)
        elif thumb_src and str(thumb_src).startswith("http"):
            def fetch():
                try:
                    r = requests.get(thumb_src, timeout=4)
                    if r.status_code == 200:
                        v_id = self.current_data.get("id") or "hero"
                        local_file = os.path.abspath(f"cache/thumbs/{v_id}.jpg")
                        with open(local_file, "wb") as f:
                            f.write(r.content)
                        self.current_data["thumbnail"] = local_file
                        new_img = create_rounded_cover(local_file, size=(140, 140), radius=16)
                        self.after(0, lambda: self.cover_lbl.configure(image=new_img))
                except Exception:
                    pass
            threading.Thread(target=fetch, daemon=True).start()
        else:
            self.cover_lbl.configure(image=create_rounded_cover("", size=(140, 140), radius=16))

    def _on_play(self):
        if self.current_data and self.play_callback:
            self.play_callback(self.current_data)

    def _on_fav(self):
        if self.current_data and self.fav_callback:
            is_now_fav = self.fav_callback(self.current_data)
            self.fav_btn.configure(
                text="♥  Liked" if is_now_fav else "♡  Favorite",
                text_color=AppStyles.ACCENT if is_now_fav else AppStyles.TEXT_WHITE
            )

class AlbumGridCard(ctk.CTkFrame):
    def __init__(self, master, data, play_cmd, fav_cmd, menu_cmd, is_fav=False, **kwargs):
        super().__init__(
            master,
            fg_color=AppStyles.BG_CARD,
            corner_radius=16,
            border_width=1,
            border_color=AppStyles.BORDER_CARD,
            width=188,
            height=330,
            **kwargs
        )
        self.pack_propagate(False)
        self.data = data
        self.play_cmd = play_cmd
        self.fav_cmd = fav_cmd
        self.menu_cmd = menu_cmd
        self.is_fav = is_fav

        self.art_wrap = ctk.CTkFrame(self, width=164, height=164, corner_radius=12, fg_color="#181B28")
        self.art_wrap.pack(padx=12, pady=(12, 8))
        self.art_wrap.pack_propagate(False)

        self.cover_lbl = ctk.CTkLabel(
            self.art_wrap,
            text="",
            image=create_rounded_cover("", size=(164, 164), radius=12),
            width=164,
            height=164
        )
        self.cover_lbl.place(relx=0.5, rely=0.5, anchor="center")
        self._load_thumbnail()

        raw_title = str(data.get("title", "Unknown")).strip()
        display_title = raw_title if len(raw_title) <= 52 else raw_title[:49] + "..."

        self.t_lbl = ctk.CTkLabel(
            self,
            text=display_title,
            font=(AppStyles.FONT, 12, "bold"),
            text_color=AppStyles.TEXT_TITLE,
            anchor="nw",
            wraplength=162,
            justify="left",
            height=38
        )
        self.t_lbl.pack(fill="x", padx=12, pady=(0, 2))

        raw_artist = str(data.get("artist", "Unknown")).strip()
        display_artist = raw_artist if len(raw_artist) <= 26 else raw_artist[:24] + "..."

        self.a_lbl = ctk.CTkLabel(
            self,
            text=display_artist,
            font=(AppStyles.FONT, 11),
            text_color=AppStyles.TEXT_MUTED,
            anchor="w",
            wraplength=162,
            justify="left"
        )
        self.a_lbl.pack(fill="x", padx=12, pady=(0, 6))

        self.actions = ctk.CTkFrame(self, fg_color="transparent", height=42)
        self.actions.pack(fill="x", padx=12, pady=(0, 10), side="bottom")
        self.actions.pack_propagate(False)

        self.play_btn = ctk.CTkButton(
            self.actions,
            text="▶",
            width=36,
            height=36,
            corner_radius=18,
            fg_color=AppStyles.ACCENT,
            hover_color=AppStyles.ACCENT_HOVER,
            text_color=AppStyles.TEXT_WHITE,
            font=(AppStyles.FONT, 13, "bold"),
            command=lambda: self.play_cmd(self.data)
        )
        self.play_btn.pack(side="left")

        self.fav_btn = ctk.CTkButton(
            self.actions,
            text="♥" if self.is_fav else "♡",
            width=34,
            height=34,
            corner_radius=17,
            fg_color="transparent",
            hover_color=AppStyles.BG_CARD_HOVER,
            text_color=AppStyles.ACCENT if self.is_fav else AppStyles.TEXT_MUTED,
            font=(AppStyles.FONT, 15),
            command=self._on_fav_click
        )
        self.fav_btn.pack(side="right")

        self.opt_btn = ctk.CTkButton(
            self.actions,
            text="⋮",
            width=30,
            height=34,
            corner_radius=15,
            fg_color="transparent",
            hover_color=AppStyles.BG_CARD_HOVER,
            text_color=AppStyles.TEXT_MUTED,
            font=(AppStyles.FONT, 16, "bold"),
            command=lambda: self.menu_cmd(self.data, self.opt_btn.winfo_rootx(), self.opt_btn.winfo_rooty() + self.opt_btn.winfo_height())
        )
        self.opt_btn.pack(side="right", padx=2)

        hover_group = [self, self.art_wrap, self.cover_lbl, self.t_lbl, self.a_lbl, self.actions]

        def on_enter(e):
            self.configure(
                fg_color=AppStyles.BG_CARD_HOVER,
                border_color=AppStyles.BORDER_ACTIVE,
                border_width=2
            )

        def on_leave(e):
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
            if widget not in hover_group and widget not in [self.play_btn, self.fav_btn, self.opt_btn]:
                self.configure(
                    fg_color=AppStyles.BG_CARD,
                    border_color=AppStyles.BORDER_CARD,
                    border_width=1
                )

        def on_click(e):
            self.play_cmd(self.data)

        def on_right_click(e):
            self.menu_cmd(self.data, e.x_root, e.y_root)

        for w in hover_group:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-3>", on_right_click)
            if w in [self, self.art_wrap, self.cover_lbl, self.t_lbl, self.a_lbl]:
                w.bind("<Button-1>", on_click)
                w.bind("<Double-Button-1>", on_click)

    def _load_thumbnail(self):
        thumb_src = self.data.get("thumbnail", "")
        if thumb_src and os.path.exists(thumb_src):
            img = create_rounded_cover(thumb_src, size=(164, 164), radius=12)
            self.cover_lbl.configure(image=img)
            return

        v_id = self.data.get("id") or ""
        if not thumb_src and v_id and len(v_id) == 11:
            thumb_src = f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"

        if thumb_src and str(thumb_src).startswith("http"):
            def download_async():
                try:
                    safe_id = v_id if v_id else "thumb"
                    dest = os.path.abspath(f"cache/thumbs/{safe_id}.jpg")
                    r = requests.get(thumb_src, timeout=4)
                    if r.status_code == 200:
                        with open(dest, "wb") as f:
                            f.write(r.content)
                        self.data["thumbnail"] = dest
                        new_img = create_rounded_cover(dest, size=(164, 164), radius=12)
                        self.after(0, lambda: self.cover_lbl.configure(image=new_img))
                except Exception:
                    pass
            threading.Thread(target=download_async, daemon=True).start()

    def _on_fav_click(self):
        new_val = self.fav_cmd(self.data)
        self.is_fav = new_val
        self.fav_btn.configure(
            text="♥" if new_val else "♡",
            text_color=AppStyles.ACCENT if new_val else AppStyles.TEXT_MUTED
        )

class TrackTableRow(ctk.CTkFrame):
    def __init__(self, master, idx, data, play_cmd, fav_cmd, save_cmd, del_cmd, is_fav=False, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            corner_radius=12,
            height=62,
            **kwargs
        )
        self.pack_propagate(False)
        self.data = data
        self.play_cmd = play_cmd
        self.fav_cmd = fav_cmd
        self.save_cmd = save_cmd
        self.del_cmd = del_cmd
        self.is_fav = is_fav

        self.bind("<Enter>", lambda e: self.configure(fg_color=AppStyles.BG_CARD_HOVER))
        self.bind("<Leave>", lambda e: self.configure(fg_color="transparent"))
        self.bind("<Double-Button-1>", lambda e: self.play_cmd(self.data))

        idx_lbl = ctk.CTkLabel(
            self,
            text=f"{idx:02d}",
            width=32,
            font=(AppStyles.FONT, 11, "bold"),
            text_color=AppStyles.TEXT_MUTED
        )
        idx_lbl.pack(side="left", padx=(10, 4))
        idx_lbl.bind("<Button-1>", lambda e: self.play_cmd(self.data))

        self.art_box = ctk.CTkLabel(
            self,
            text="",
            image=create_rounded_cover("", size=(44, 44), radius=10),
            width=44,
            height=44
        )
        self.art_box.pack(side="left", padx=8)
        self.art_box.bind("<Button-1>", lambda e: self.play_cmd(self.data))
        self._load_row_thumbnail()

        info_box = ctk.CTkFrame(self, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        info_box.bind("<Button-1>", lambda e: self.play_cmd(self.data))

        t_lbl = ctk.CTkLabel(
            info_box,
            text=data.get("title", "Unknown"),
            font=(AppStyles.FONT, 13, "bold"),
            text_color=AppStyles.TEXT_TITLE,
            anchor="w",
            wraplength=480,
            justify="left"
        )
        t_lbl.pack(fill="x")
        t_lbl.bind("<Button-1>", lambda e: self.play_cmd(self.data))

        a_lbl = ctk.CTkLabel(
            info_box,
            text=data.get("artist", "Unknown"),
            font=(AppStyles.FONT, 11),
            text_color=AppStyles.TEXT_MUTED,
            anchor="w",
            wraplength=480,
            justify="left"
        )
        a_lbl.pack(fill="x")
        a_lbl.bind("<Button-1>", lambda e: self.play_cmd(self.data))

        self.menu = Menu(self, tearoff=0, bg=AppStyles.BG_CARD, fg="white",
                         activebackground=AppStyles.ACCENT, activeforeground="white",
                         relief="flat", bd=0)
        self.menu.add_command(label="Play Now", command=lambda: self.play_cmd(self.data))
        self.menu.add_command(label="Play Next", command=lambda: self.winfo_toplevel().add_to_queue(self.data))
        self.menu.add_command(label="Add to Playlist...", command=lambda: self.winfo_toplevel().prompt_add_to_playlist(self.data))
        self.menu.add_separator()
        self.menu.add_command(label="Delete / Remove", command=lambda: self.del_cmd(self.data))

        self.opt_btn = ctk.CTkButton(
            self,
            text="⋮",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color=AppStyles.BG_INPUT,
            text_color=AppStyles.TEXT_MUTED,
            font=(AppStyles.FONT, 16, "bold"),
            command=self._show_menu_from_btn
        )
        self.opt_btn.pack(side="right", padx=(2, 12))

        src_badge = ctk.CTkLabel(
            self,
            text="STREAM" if data.get("source") == "STREAM" else "LOCAL",
            font=(AppStyles.FONT, 9, "bold"),
            fg_color=AppStyles.ACCENT_DIM if data.get("source") == "STREAM" else "#1F2338",
            text_color=AppStyles.ACCENT if data.get("source") == "STREAM" else AppStyles.SECONDARY,
            corner_radius=6,
            width=64,
            height=20
        )
        src_badge.pack(side="right", padx=8)

        dur_lbl = ctk.CTkLabel(
            self,
            text=format_time(data.get("duration", 0)),
            font=(AppStyles.FONT, 12),
            text_color=AppStyles.TEXT_MUTED,
            width=46
        )
        dur_lbl.pack(side="right", padx=6)

        if data.get("source") == "STREAM":
            dl_btn = ctk.CTkButton(
                self,
                text="↓",
                width=28,
                height=28,
                corner_radius=14,
                fg_color="transparent",
                hover_color=AppStyles.BG_INPUT,
                text_color=AppStyles.TEXT_BODY,
                font=(AppStyles.FONT, 14, "bold"),
                command=lambda: self.save_cmd(self.data)
            )
            dl_btn.pack(side="right", padx=3)

        self.fav_btn = ctk.CTkButton(
            self,
            text="♥" if self.is_fav else "♡",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color=AppStyles.BG_INPUT,
            text_color=AppStyles.ACCENT if self.is_fav else AppStyles.TEXT_MUTED,
            font=(AppStyles.FONT, 14),
            command=self._on_fav_toggle
        )
        self.fav_btn.pack(side="right", padx=3)

        play_act = ctk.CTkButton(
            self,
            text="▶",
            width=32,
            height=32,
            corner_radius=16,
            fg_color=AppStyles.BG_INPUT,
            hover_color=AppStyles.ACCENT,
            text_color=AppStyles.TEXT_TITLE,
            font=(AppStyles.FONT, 12, "bold"),
            command=lambda: self.play_cmd(self.data)
        )
        play_act.pack(side="right", padx=6)

        def post_menu(evt):
            self.menu.post(evt.x_root, evt.y_root)

        for w in (self, info_box, t_lbl, a_lbl, self.art_box, idx_lbl, dur_lbl, src_badge):
            w.bind("<Button-3>", post_menu)

    def _load_row_thumbnail(self):
        thumb_src = self.data.get("thumbnail", "")
        if thumb_src and os.path.exists(thumb_src):
            img = create_rounded_cover(thumb_src, size=(44, 44), radius=10)
            self.art_box.configure(image=img)
            return

        v_id = self.data.get("id") or ""
        if not thumb_src and v_id and len(v_id) == 11:
            thumb_src = f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"

        if thumb_src and str(thumb_src).startswith("http"):
            def download_async():
                try:
                    safe_id = v_id if v_id else "thumb"
                    dest = os.path.abspath(f"cache/thumbs/{safe_id}.jpg")
                    r = requests.get(thumb_src, timeout=4)
                    if r.status_code == 200:
                        with open(dest, "wb") as f:
                            f.write(r.content)
                        self.data["thumbnail"] = dest
                        new_img = create_rounded_cover(dest, size=(44, 44), radius=10)
                        self.after(0, lambda: self.art_box.configure(image=new_img))
                except Exception:
                    pass
            threading.Thread(target=download_async, daemon=True).start()

    def _show_menu_from_btn(self):
        x = self.opt_btn.winfo_rootx()
        y = self.opt_btn.winfo_rooty() + self.opt_btn.winfo_height()
        self.menu.post(x, y)

    def _on_fav_toggle(self):
        new_val = self.fav_cmd(self.data)
        self.is_fav = new_val
        self.fav_btn.configure(
            text="♥" if new_val else "♡",
            text_color=AppStyles.ACCENT if new_val else AppStyles.TEXT_MUTED
        )

class ModernSearchArea(ctk.CTkFrame):
    def __init__(self, master, search_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.box = ctk.CTkFrame(
            self,
            fg_color=AppStyles.BG_INPUT,
            height=46,
            corner_radius=23,
            border_width=1,
            border_color=AppStyles.BORDER_CARD
        )
        self.box.pack(fill="x", expand=True)
        self.box.pack_propagate(False)

        ctk.CTkLabel(
            self.box,
            text="🔍",
            font=(AppStyles.FONT, 13)
        ).pack(side="left", padx=(16, 8))

        self.entry = ctk.CTkEntry(
            self.box,
            placeholder_text="Search songs, albums, artists, or paste a streaming URL...",
            border_width=0,
            fg_color="transparent",
            text_color=AppStyles.TEXT_TITLE,
            placeholder_text_color=AppStyles.TEXT_MUTED,
            font=(AppStyles.FONT, 13)
        )
        self.entry.pack(side="left", fill="both", expand=True)
        self.entry.bind("<Return>", lambda e: search_callback())

        self.btn = ctk.CTkButton(
            self.box,
            text="Search",
            width=85,
            height=32,
            corner_radius=16,
            fg_color=AppStyles.ACCENT,
            text_color=AppStyles.TEXT_WHITE,
            hover_color=AppStyles.ACCENT_HOVER,
            font=(AppStyles.FONT, 12, "bold"),
            command=search_callback
        )
        self.btn.pack(side="right", padx=7)

    def get(self):
        return self.entry.get().strip()

    def set_text(self, txt):
        self.entry.delete(0, 'end')
        self.entry.insert(0, txt)

    def set_state(self, st):
        self.entry.configure(state=st)
        self.btn.configure(state=st)

class SidebarNavButton(ctk.CTkButton):
    def __init__(self, master, text, icon, command, is_active=False, **kwargs):
        super().__init__(
            master,
            text=f"   {icon}   {text}",
            command=command,
            fg_color=AppStyles.BG_CARD if is_active else "transparent",
            text_color=AppStyles.ACCENT if is_active else AppStyles.TEXT_BODY,
            hover_color=AppStyles.BG_CARD_HOVER,
            anchor="w",
            font=(AppStyles.FONT, 12, "bold" if is_active else "normal"),
            height=38,
            corner_radius=10,
            border_width=1 if is_active else 0,
            border_color=AppStyles.BORDER_CARD,
            **kwargs
        )