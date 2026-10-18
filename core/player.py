import pygame
import os

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        self.is_paused = False
        self.current_file = None
        self.start_offset = 0.0
        self.volume = 0.8
        pygame.mixer.music.set_volume(self.volume)

    def play(self, file_path, start_time=0.0):
        try:
            if not os.path.exists(file_path):
                return False
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(start=int(start_time))
            self.current_file = file_path
            self.start_offset = float(start_time)
            self.is_paused = False
            return True
        except Exception:
            return False

    def toggle_pause(self):
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            pygame.mixer.music.pause()
            self.is_paused = True
        return self.is_paused

    def seek(self, seconds):
        if self.current_file and os.path.exists(self.current_file):
            return self.play(self.current_file, start_time=seconds)
        return False

    def stop(self):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        self.is_paused = False
        self.start_offset = 0.0

    def set_volume(self, val):
        self.volume = max(0.0, min(1.0, float(val)))
        pygame.mixer.music.set_volume(self.volume)

    def get_pos(self):
        if not pygame.mixer.music.get_busy() and not self.is_paused:
            return 0.0
        pos = pygame.mixer.music.get_pos()
        if pos < 0:
            return self.start_offset
        return self.start_offset + (pos / 1000.0)

    def is_active(self):
        return pygame.mixer.music.get_busy() or self.is_paused