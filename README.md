# 🎵 PulseStream
### Developed by Nethru Randev

**PulseStream** is a high-performance, professional-grade desktop music application. It features a sleek, industry-standard **OLED-Dark** interface inspired by Spotify and Apple Music. Built for modern desktop environments, PulseStream allows users to stream music globally via YouTube, manage local audio libraries, and identify unknown songs using AI-powered recognition.

---

## 🚀 Key Features

*   **Next-Level Modern GUI:** A minimalist interface built with `CustomTkinter`, featuring a floating player "pill," high-density track cards, and smooth hover animations.
*   **Global Music Streaming:** Search for any track or paste YouTube URLs directly. PulseStream handles the extraction and caching for a seamless experience.
*   **Local Library Management:** High-fidelity playback for your own `.mp3`, `.wav`, and `.ogg` files.
*   **AI Song Identification:** Integrated "Identify" feature (powered by Shazam) that records 7 seconds of ambient audio to detect song metadata.
*   **Optimized Performance:** Multi-threaded architecture ensures the UI remains responsive even during heavy downloads or audio processing.
*   **Pure OLED Design:** Deep black and gray palette designed for high-contrast displays to reduce eye strain.

---

## 🛠 Tech Stack

*   **Language:** Python 3.9+ (Fully compatible with 3.13)
*   **GUI Framework:** `CustomTkinter`
*   **Audio Engine:** `Pygame (mixer)`
*   **Streaming/Extraction:** `yt-dlp`
*   **Recognition/ID:** `Shazamio` & `PyAudio`
*   **Media Processing:** `FFmpeg`
*   **UI Assets:** `Pillow` (PIL)

---

## 📦 System Requirements & Setup

### 1. FFmpeg (Mandatory)
PulseStream requires FFmpeg to convert YouTube streams into playable audio.
*   Download the **Essentials Build** from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip).
*   Extract the zip and copy **`ffmpeg.exe`** and **`ffprobe.exe`** from the `bin` folder directly into your `PulseStream/` root directory.

### 2. Node.js (Highly Recommended)
YouTube frequently updates its security. Installing [Node.js](https://nodejs.org/) allows `yt-dlp` to solve JavaScript signatures, preventing errors and ensuring fast streaming.

### 3. Python Dependencies
Install all required libraries using:
```bash
pip install customtkinter pygame yt-dlp shazamio pyaudio pillow pydub
```

---

## 📂 Project Structure

```text
PulseStream/
│
├── main.py                # Main Application Entry Point
├── ffmpeg.exe             # Media Conversion Binary
├── ffprobe.exe            # Media Metadata Binary
├── cache/                 # Cached Streaming Data (Auto-generated)
│
├── core/                  # Audio Engines
│   ├── player.py          # Playback logic (Pygame)
│   └── recorder.py        # Recording logic (PyAudio)
│
├── services/              # API & Network Services
│   ├── searcher.py        # YouTube Streaming & Search service
│   └── recognizer.py      # Shazam Identification service
│
├── ui/                    # Presentation Layer
│   ├── components.py      # Modern Custom Widgets
│   └── styles.py          # OLED Palette & Fonts
│
└── utils/                 # Utilities
    └── helpers.py         # Directory & Path handlers
```

---

## 🎮 How to Use

1.  **Launch:** Run `python main.py`.
2.  **Discover:** Type a song name in the search bar and press `Enter`. The track will appear in your "Your Tracks" list.
3.  **Library:** Click **📂 Library** in the sidebar to add local music from your computer.
4.  **Identify:** Click **🎙 Identify** to discover a song playing in your room. PulseStream will display the result after 7 seconds.
5.  **Control:** Use the floating pill at the bottom to Play, Pause, or adjust Volume.

---

## 🔧 Troubleshooting

*   **UI Issues:** PulseStream is optimized for 1250x850. If elements appear overlapped, ensure your Windows Display Scaling is set to 100%.
*   **Streaming Errors:** If search results fail, update the core extractor: `pip install -U yt-dlp`.
*   **Recognition Fails:** Ensure your microphone is enabled in your OS System Settings.

---

## 📜 Disclaimer
*This software is intended for personal and educational use. Please respect copyright laws and the terms of service of third-party platforms.*