import pygame
import os

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_track = None
        self.is_paused = False

    def play(self, file_path):
        if not os.path.exists(file_path):
            print("File not found")
            return
        
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        self.current_track = file_path
        self.is_paused = False

    def toggle_pause(self):
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            pygame.mixer.music.pause()
            self.is_paused = True

    def stop(self):
        pygame.mixer.music.stop()

    def set_volume(self, val):
        pygame.mixer.music.set_volume(float(val) / 100)