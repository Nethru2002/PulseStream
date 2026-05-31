import customtkinter as ctk
from ui.styles import AppStyles

class SidebarButton(ctk.CTkButton):
    def __init__(self, master, text, icon, command, **kwargs):
        super().__init__(
            master, 
            text=f"   {icon}    {text}", 
            command=command,
            fg_color="transparent", 
            text_color="#B3B3B3",
            hover_color="#1A1A1A", 
            anchor="w", 
            font=("Inter", 13, "bold"),
            height=50, 
            corner_radius=12, 
            **kwargs
        )

class TrackRow(ctk.CTkFrame):
    def __init__(self, master, title, artist, tag, play_cmd, **kwargs):
        super().__init__(master, fg_color="transparent", height=80, **kwargs)
        self.pack_propagate(False)
        self.play_cmd = play_cmd

        self.inner = ctk.CTkFrame(self, fg_color="#181818", corner_radius=15)
        self.inner.pack(fill="x", padx=10, pady=5)

        self.art = ctk.CTkFrame(self.inner, width=50, height=50, fg_color="#282828", corner_radius=8)
        self.art.pack(side="left", padx=15, pady=10)
        self.art.pack_propagate(False)
        ctk.CTkLabel(self.art, text="🎵", font=("Inter", 16)).place(relx=0.5, rely=0.5, anchor="center")

        info_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        info_frame.pack(side="left", fill="y", pady=12)
        
        ctk.CTkLabel(info_frame, text=title[:45], font=("Inter", 14, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=artist, font=("Inter", 11), text_color="#888888").pack(anchor="w")

        ctk.CTkLabel(self.inner, text=tag, font=("Inter", 10, "bold"), fg_color="#333333", 
                     text_color="#AAAAAA", corner_radius=6, width=75, height=24).pack(side="right", padx=25)

        self.inner.bind("<Enter>", lambda e: self.inner.configure(fg_color="#222222"))
        self.inner.bind("<Leave>", lambda e: self.inner.configure(fg_color="#181818"))
        self.inner.bind("<Button-1>", lambda e: self.play_cmd())