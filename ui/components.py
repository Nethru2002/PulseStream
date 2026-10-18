import os
import random
import customtkinter as ctk
from tkinter import Canvas, Menu
from PIL import Image, ImageDraw, ImageOps
from ui.styles import AppStyles
from utils.helpers import format_time

def create_rounded_cover(image_path_or_obj, size=(50, 50), radius=10):
    try:
        if isinstance(image_path_or_obj, str):
            if not image_path_or_obj or not os.path.exists(image_path_or_obj):
                img = Image.new("RGBA", size, color="#1E1E28")
            else:
                img = Image.open(image_path_or_obj).convert("RGBA")
        elif image_path_or_obj is None:
            img = Image.new("RGBA", size, color="#1E1E28")
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
        fallback = Image.new("RGBA", size, color="#1E1E28")
        return ctk.CTkImage(light_image=fallback, dark_image=fallback, size=size)

class AnimatedVisualizer(Canvas):
    def __init__(self, master, width=120, height=36, bar_count=7, **kwargs):
        super().__init__(
            master,
            width=width,
            height=height,
            bg=AppStyles.BG_PLAYER,
            highlightthickness=0,
            **kwargs
        )
        self.width = width
        self.height = height
        self.bar_count = bar_count
        self.is_active = False
        self.bars = []
        bar_width = (width - ((bar_count - 1) * 3)) / bar_count
        for i in range(bar_count):
            x1 = i * (bar_width + 3)
            x2 = x1 + bar_width
            rect = self.create_rectangle(x1, height - 4, x2, height, fill=AppStyles.ACCENT, width=0)
            self.bars.append((rect, x1, x2))

    def set_playing(self, is_playing):
        self.is_active = is_playing
        if not is_playing:
            self._reset_bars()

    def update_bars(self):
        if not self.is_active:
            return
        for rect, x1, x2 in self.bars:
            h = random.randint(4, self.height)
            self.coords(rect, x1, self.height - h, x2, self.height)

    def _reset_bars(self):
        for rect, x1, x2 in self.bars:
            self.coords(rect, x1, self.height - 4, x2, self.height)

class HeroBanner(ctk.CTkFrame):
    def __init__(self, master, play_callback, **kwargs):
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
        self.current_data = None

        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.pack(fill="both", expand=True, padx=28, pady=24)

        self.meta_box = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.meta_box.pack(side="left", fill="both", expand=True)

        self.tag_lbl = ctk.CTkLabel(
            self.meta_box,
            text="FEATURED EXPERIENCE",
            font=(AppStyles.FONT, 10, "bold"),
            text_color=AppStyles.ACCENT
        )
        self.tag_lbl.pack(anchor="w")

        self.title_lbl = ctk.CTkLabel(
            self.meta_box,
            text="Discover Infinite Soundscapes",
            font=(AppStyles.FONT, 28, "bold"),
            text_color=AppStyles.TEXT_WHITE
        )
        self.title_lbl.pack(anchor="w", pady=(6, 2))

        self.sub_lbl = ctk.CTkLabel(
            self.meta_box,
            text="High-resolution audio streaming with synchronized lyrics and lossless cache.",
            font=(AppStyles.FONT, 13),
            text_color=AppStyles.TEXT_MED
        )
        self.sub_lbl.pack(anchor="w")

        self.btn_row = ctk.CTkFrame(self.meta_box, fg_color="transparent")
        self.btn_row.pack(anchor="w", pady=(18, 0))

        self.hero_play_btn = ctk.CTkButton(
            self.btn_row,
            text="▶  Play Selection",
            width=150,
            height=40,
            corner_radius=20,
            fg_color=AppStyles.ACCENT,
            text_color="#000000",
            hover_color=AppStyles.ACCENT_HOVER,
            font=(AppStyles.FONT, 13, "bold"),
            command=self._on_play
        )
        self.hero_play_btn.pack(side="left")

    def update_hero(self, track_data):
        self.current_data = track_data
        self.tag_lbl.configure(text="NOW HEADLINING")
        self.title_lbl.configure(text=track_data.get("title", "")[:35])
        self.sub_lbl.configure(text=f"Artist: {track_data.get('artist', 'Various Artists')}  •  Pulse Lossless Stream")

    def _on_play(self):
        if self.current_data and self.play_callback:
            self.play_callback(self.current_data)

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
            placeholder_text="Search songs, artists, global charts, or paste YouTube link...",
            border_width=0,
            fg_color="transparent",
            text_color=AppStyles.TEXT_WHITE,
            placeholder_text_color=AppStyles.TEXT_MUTED,
            font=(AppStyles.FONT, 13)
        )
        self.entry.pack(side="left", fill="both", expand=True)
        self.entry.bind("<Return>", lambda e: search_callback())

        self.btn = ctk.CTkButton(
            self.box,
            text="Explore",
            width=85,
            height=32,
            corner_radius=16,
            fg_color=AppStyles.ACCENT,
            text_color="#000000",
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
            text=f"   {icon}    {text}",
            command=command,
            fg_color=AppStyles.BG_CARD if is_active else "transparent",
            text_color=AppStyles.TEXT_WHITE if is_active else AppStyles.TEXT_MED,
            hover_color=AppStyles.BG_CARD_HOVER,
            anchor="w",
            font=(AppStyles.FONT, 13, "bold" if is_active else "normal"),
            height=42,
            corner_radius=10,
            border_width=1 if is_active else 0,
            border_color=AppStyles.BORDER_CARD,
            **kwargs
        )

class TrackTableRow(ctk.CTkFrame):
    def __init__(self, master, idx, data, play_cmd, fav_cmd, save_cmd, del_cmd, is_fav=False, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            corner_radius=10,
            height=58,
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
            width=36,
            font=(AppStyles.FONT, 12, "bold"),
            text_color=AppStyles.TEXT_MUTED
        )
        idx_lbl.pack(side="left", padx=(10, 4))
        idx_lbl.bind("<Button-1>", lambda e: self.play_cmd(self.data))

        self.art_box = ctk.CTkLabel(
            self,
            text="",
            image=create_rounded_cover(data.get("thumbnail", ""), size=(42, 42), radius=8),
            width=42,
            height=42
        )
        self.art_box.pack(side="left", padx=8)
        self.art_box.bind("<Button-1>", lambda e: self.play_cmd(self.data))

        info_box = ctk.CTkFrame(self, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        info_box.bind("<Button-1>", lambda e: self.play_cmd(self.data))

        t_lbl = ctk.CTkLabel(
            info_box,
            text=data.get("title", "Unknown")[:44],
            font=(AppStyles.FONT, 13, "bold"),
            text_color=AppStyles.TEXT_WHITE,
            anchor="w"
        )
        t_lbl.pack(fill="x")
        t_lbl.bind("<Button-1>", lambda e: self.play_cmd(self.data))

        a_lbl = ctk.CTkLabel(
            info_box,
            text=data.get("artist", "Unknown")[:32],
            font=(AppStyles.FONT, 11),
            text_color=AppStyles.TEXT_MUTED,
            anchor="w"
        )
        a_lbl.pack(fill="x")
        a_lbl.bind("<Button-1>", lambda e: self.play_cmd(self.data))

        src_badge = ctk.CTkLabel(
            self,
            text=data.get("source", "LOCAL"),
            font=(AppStyles.FONT, 9, "bold"),
            fg_color=AppStyles.BG_INPUT,
            text_color=AppStyles.ACCENT if data.get("source") == "STREAM" else AppStyles.SECONDARY,
            corner_radius=6,
            width=58,
            height=20
        )
        src_badge.pack(side="right", padx=12)

        dur_lbl = ctk.CTkLabel(
            self,
            text=format_time(data.get("duration", 0)),
            font=(AppStyles.FONT, 12),
            text_color=AppStyles.TEXT_MED,
            width=48
        )
        dur_lbl.pack(side="right", padx=8)

        if data.get("source") == "STREAM":
            dl_btn = ctk.CTkButton(
                self,
                text="↓",
                width=28,
                height=28,
                corner_radius=14,
                fg_color="transparent",
                hover_color=AppStyles.BG_INPUT,
                text_color=AppStyles.TEXT_MED,
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
            text_color=AppStyles.DANGER if self.is_fav else AppStyles.TEXT_MUTED,
            font=(AppStyles.FONT, 14),
            command=self._on_fav_toggle
        )
        self.fav_btn.pack(side="right", padx=3)

        play_act = ctk.CTkButton(
            self,
            text="▶",
            width=30,
            height=30,
            corner_radius=15,
            fg_color=AppStyles.BG_INPUT,
            hover_color=AppStyles.ACCENT,
            text_color=AppStyles.TEXT_WHITE,
            font=(AppStyles.FONT, 11, "bold"),
            command=lambda: self.play_cmd(self.data)
        )
        play_act.pack(side="right", padx=6)

        self.menu = Menu(self, tearoff=0, bg=AppStyles.BG_CARD, fg="white",
                         activebackground=AppStyles.ACCENT, activeforeground="black",
                         relief="flat", bd=0)
        self.menu.add_command(label="Play Next", command=lambda: self.master.master.master.add_to_queue(self.data))
        self.menu.add_separator()
        self.menu.add_command(label="Delete / Remove", command=lambda: self.del_cmd(self.data))
        self.bind("<Button-3>", lambda e: self.menu.post(e.x_root, e.y_root))

    def _on_fav_toggle(self):
        new_val = self.fav_cmd(self.data)
        self.is_fav = new_val
        self.fav_btn.configure(
            text="♥" if new_val else "♡",
            text_color=AppStyles.DANGER if new_val else AppStyles.TEXT_MUTED
        )