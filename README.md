# 🎵 PulseStream
### **Developed by Nethru Randev**

**PulseStream** is a high-performance, professional-grade desktop music application designed for a premium listening experience. It features a sophisticated **OLED-Dark** interface, combining global YouTube streaming, local file management, and AI-powered song recognition into a single, seamless dashboard.

---

## 🚀 Key Features

*   **Next-Level Modern GUI:** Built with `CustomTkinter`, featuring a floating "Pill" player, rounded glassmorphism track cards, and smooth hover animations.
*   **Global Music Streaming:** Search for any track or artist. PulseStream extracts, streams, and caches audio for high-quality playback.
*   **Local Library:** Full support for `.mp3`, `.wav`, and `.ogg` files stored on your computer.
*   **AI Song Identification:** Integrated "Identify" tool powered by Shazam. Records 7 seconds of ambient audio to find titles and artists.
*   **Advanced Playback Controls:**
    *   **Smooth Seeking:** A real-time progress slider for rewinding/fast-forwarding tracks.
    *   **Precise Volume:** Logarithmic volume scaling.
    *   **Context Menu:** Right-click any song to "Bring to Front" or "Send to Back" to manage your session queue.
*   **Permanent Downloads:** Dedicated download button to save streamed tracks from the cache to your permanent local storage.
*   **Optimized Performance:** Multi-threaded processing ensures the UI never freezes during downloads or song recognition.

---

## 📂 Project Structure

Following the professional modular architecture:

```text
PULSESTREAM/
│
├── core/                  # Audio Engine Layer
│   ├── __init__.py
│   ├── player.py          # Pygame-based playback & seeking logic
│   └── recorder.py        # PyAudio microphone recording logic
│
├── services/              # API & Service Layer
│   ├── __init__.py
│   ├── recognizer.py      # Shazam API song identification
│   └── searcher.py        # YouTube extraction & metadata service
│
├── ui/                    # Presentation Layer
│   ├── __init__.py
│   ├── components.py      # Custom widgets (SearchArea, TrackRow, etc.)
│   └── styles.py          # Professional OLED color palette
│
├── utils/                 # Utility Layer
│   ├── __init__.py
│   └── helpers.py         # Path handling and directory management
│
├── cache/                 # Temporary storage for streamed tracks
├── database.db            # Local data persistence
├── ffmpeg.exe             # Core binary for audio conversion
├── ffprobe.exe            # Media metadata analyzer
├── main.py                # Application Entry Point & Layout Manager
├── requirements.txt       # List of Python dependencies
└── README.md              # Project documentation
```

---

## 🛠 Tech Stack

*   **GUI:** `CustomTkinter`
*   **Audio Engine:** `Pygame (mixer)`
*   **Streaming:** `yt-dlp`
*   **Identification:** `Shazamio` & `PyAudio`
*   **Metadata/Seeking:** `Mutagen`
*   **Media Processing:** `FFmpeg`
*   **Image Handling:** `Pillow`

---

## 📦 System Requirements & Setup

### 1. FFmpeg (Mandatory)
PulseStream requires **ffmpeg.exe** and **ffprobe.exe** to be present in the root folder (as shown in the structure above) to handle YouTube audio conversion.

### 2. Node.js (Highly Recommended)
Install [Node.js](https://nodejs.org/) to allow the streaming engine to bypass YouTube's signature protection for faster and more reliable searching.

### 3. Installation
Install all required Python libraries via pip:
```powershell
pip install customtkinter pygame yt-dlp shazamio pyaudio pillow pydub mutagen
```

---

## 🎮 How to Use

1.  **Run the App:** Execute `python main.py`.
2.  **Search & Stream:** Type a song name in the top search bar and click the **Search** button. The track will appear in "Your Tracks."
3.  **Local Files:** Click **📂 Library** in the sidebar to add files from your PC.
4.  **Identify Music:** Click **🎙 Identify Song**. The app will listen for 7 seconds and display the result.
5.  **Playback:** 
    *   **Double-Click** or click a song row to play.
    *   Use the **Floating Pill Player** to play/pause.
    *   **Drag the slider** to rewind or skip to any part of the song.
    *   **Right-Click** a track to move it to the top or bottom of the list.
6.  **Download:** Click the **📥 icon** on any streamed track to save it permanently to your computer.

---

## 🔧 Troubleshooting

*   **Search/Stream Fails:** Update the extractor logic using `pip install -U yt-dlp`.
*   **No Sound/Audio Lockup:** Ensure `ffmpeg.exe` is in the root folder and not blocked by antivirus.
*   **Blue Highlight on Search:** PulseStream includes an "Anti-Focus" logic, but if it persists, simply click anywhere on the sidebar to clear the highlight.

---

## 📜 Disclaimer
*PulseStream is developed for educational and personal use. Please respect copyright laws and the terms of service of content providers.*

**© 2024 PulseStream | Developed by Nethru Randev**