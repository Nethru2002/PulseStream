import customtkinter as ctk
from ui.styles import AppStyles
from tkinter import Menu

class ModernSearchArea(ctk.CTkFrame):
    def __init__(self, master, search_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.container = ctk.CTkFrame(self, fg_color="transparent", height=50)
        self.container.pack(fill="x", expand=True)
        self.container.pack_propagate(False) 
        
        self.entry = ctk.CTkEntry(self.container, placeholder_text="Search for music...",
                                  border_width=0, corner_radius=25,
                                  fg_color="#1F1F1F", text_color="white", 
                                  placeholder_text_color="#888888",
                                  font=("Inter", 14))
        self.entry.pack(side="left", fill="both", expand=True)
        
        self.search_btn = ctk.CTkButton(self.container, text="Search", width=120,
                                        corner_radius=25, fg_color=AppStyles.ACCENT,
                                        text_color="black", font=("Inter", 14, "bold"),
                                        hover_color="#169c46", command=search_callback)
        self.search_btn.pack(side="left", padx=(15, 0), fill="y")

    def get(self):
        return self.entry.get()

    def set_state(self, state):
        self.entry.configure(state=state)
        self.search_btn.configure(state=state)

class SidebarButton(ctk.CTkButton):
    def __init__(self, master, text, icon, command, **kwargs):
        super().__init__(
            master, text=f"  {icon}   {text}", command=command,
            fg_color="transparent", text_color="#B3B3B3",
            hover_color="#1A1A1A", anchor="w", font=("Inter", 13, "bold"),
            height=45, corner_radius=10, **kwargs
        )

class TrackRow(ctk.CTkFrame):
    def __init__(self, master, data, tag, play_cmd, download_cmd, front_cmd, back_cmd, **kwargs):
        super().__init__(master, fg_color="transparent", height=85, **kwargs)
        self.pack_propagate(False)
        self.data = data
        self.play_cmd = play_cmd
        
        self.inner = ctk.CTkFrame(self, fg_color="#121212", corner_radius=15)
        self.inner.pack(fill="x", padx=15, pady=5)
        
        self.art = ctk.CTkFrame(self.inner, width=55, height=55, fg_color="#222222", corner_radius=8)
        self.art.pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(self.art, text="🎵", font=("Inter", 18)).place(relx=0.5, rely=0.5, anchor="center")
        
        info_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        info_frame.pack(side="left", fill="y", pady=15)
        ctk.CTkLabel(info_frame, text=data['title'][:40], font=("Inter", 14, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=data.get('artist', 'Unknown'), font=("Inter", 11), text_color="#707070").pack(anchor="w")

        if tag == "STREAM":
            ctk.CTkButton(self.inner, text="📥", width=35, height=35, corner_radius=10,
                          fg_color="#222222", hover_color="#333333", command=download_cmd).pack(side="right", padx=10)

        ctk.CTkLabel(self.inner, text=tag, font=("Inter", 10), fg_color="#252525", 
                     text_color="#888888", corner_radius=5, width=70).pack(side="right", padx=10)
        
        self.inner.bind("<Button-1>", lambda e: self.play_cmd())
        self.menu = Menu(self, tearoff=0, bg="#181818", fg="white", activebackground=AppStyles.ACCENT)
        self.menu.add_command(label="Bring to Front", command=lambda: front_cmd(self.data))
        self.menu.add_command(label="Send to Back", command=lambda: back_cmd(self.data))
        self.inner.bind("<Button-3>", lambda e: self.menu.post(e.x_root, e.y_root))