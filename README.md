# 🎵 PulseStream
### Developed by Nethru Randev

**PulseStream** is a high-performance, professional-grade desktop music suite. It combines the aesthetic elegance of modern platforms like Spotify and Apple Music with powerful utility features like AI song identification, global streaming extraction, and seamless local library management. 

Designed with a modular architecture, PulseStream is built to be fast, responsive, and visually immersive, featuring a "Zero-Overlap" Grid layout and a floating "Pill" player bar.

---

## 🚀 Key Features

*   **Next-Level Modern GUI:** A minimalist interface engineered with `CustomTkinter`, featuring a floating player bar, high-density track cards, and smooth hover animations.
*   **Unified Search & Stream:** A redesigned search area featuring a dedicated **Search Button**. Search for any song or artist, and PulseStream will fetch and stream the high-quality audio instantly.
*   **AI Song Identification:** Powered by the Shazam API. The tool listens through your microphone for 7 seconds to identify unknown tracks.
*   **NEW: Instant Stream from ID:** After identifying a song, PulseStream prompts the user to stream the song immediately, bridging the gap between discovery and listening.
*   **Advanced Playback Controls:**
    *   **Precise Seeking:** A smooth progress slider allows you to rewind or skip to any position in a track.
    *   **Dynamic Volume:** Real-time volume scaling optimized to prevent audio engine lockup.
*   **Download Manager:** Streamed songs can be permanently saved to your computer as `.mp3` files with a single click (📥).
*   **Queue Management:** Right-click context menus on any track allow you to organize your session by bringing tracks to the **Front** or sending them to the **Back** of the list.

---

## 🛠 Tech Stack

*   **GUI Framework:** `CustomTkinter` (Premium-themed modern widgets).
*   **Audio Engine:** `Pygame (mixer)` (Low-latency processing).
*   **Metadata & Logic:** `Mutagen` (Track duration and precise seeking).
*   **Streaming Extraction:** `yt-dlp` (High-speed YouTube data handling).
*   **AI Recognition:** `Shazamio` & `PyAudio`.
*   **Media Processing:** `FFmpeg` (Required binary for audio conversion).
*   **Language:** Python 3.9+ (Optimized for 3.13.x).

---

## 📦 System Requirements & Setup

### 1. Mandatory Binaries (FFmpeg)
PulseStream requires **FFmpeg** to convert internet data into playable audio.
*   Download the **Essentials Build** from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip).
*   Place `ffmpeg.exe` and `ffprobe.exe` directly in the **root folder** of the project.

### 2. JavaScript Runtime (Node.js)
To bypass modern security signatures on streaming platforms and ensure fast results, [Node.js](https://nodejs.org/) should be installed on your system.

### 3. Python Dependencies
Install all required libraries via pip:
```bash
pip install customtkinter pygame yt-dlp shazamio pyaudio pillow pydub mutagen
```

---

## 📂 Project Architecture

```text
PulseStream/
│
├── main.py                # Entry Point (Layout & Player Logic)
├── ffmpeg.exe             # Media Conversion Binary
├── ffprobe.exe            # Metadata Binary
├── cache/                 # Temporary streaming storage
│
├── core/                  # Audio Engines
│   ├── player.py          # Playback & Seeking wrapper
│   └── recorder.py        # Microphone Recording logic
│
├── services/              # API & Network Services
│   ├── searcher.py        # Streaming extraction service
│   └── recognizer.py      # AI Song Identification service
│
├── ui/                    # Design Layer
│   ├── components.py      # Modern Custom Widgets (Search, Rows, etc.)
│   └── styles.py          # OLED Palette & Typography
│
└── utils/                 # Utilities
    └── helpers.py         # Directory & File management
```

---

## 🎮 How to Use

1.  **Launch:** Run `python main.py`.
2.  **Discover:** Type a song name and click the **Search** button.
3.  **Identify:** Click **🎙 Identify Song**. Once a song is found, click **Yes** on the popup to start streaming it instantly.
4.  **Manage:** 
    *   **Double-Click** a track to play.
    *   **Right-Click** to move tracks to the front/back of the list.
    *   **Click 📥** to download a streamed song permanently.
5.  **Seek:** Click or drag the progress bar above the play button to rewind or skip sections of the song.

---

## 🔧 Troubleshooting

*   **UI Alignment:** PulseStream is optimized for a resolution of 1280x920. If elements appear overlapped, ensure Windows Display Scaling is at 100%.
*   **Audio Engine Errors:** If audio fails to resume after a seek, the engine automatically resets the buffer using the `music.unload()` command.
*   **Blue Highlight:** An internal "Focus Hijack" script removes the blue highlight from the search bar 500ms after the app starts.

---

## 📜 Disclaimer
*This software is developed for personal and educational use. Users are responsible for complying with the terms of service of third-party platforms and local copyright laws.*