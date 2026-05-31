import pygame

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.is_paused = False
        self.current_file = None

    def play(self, file_path, start_time=0):
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(start=start_time)
            self.current_file = file_path
            self.is_paused = False
        except Exception as e:
            print(f"Engine Error: {e}")

    def toggle_pause(self):
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            pygame.mixer.music.pause()
            self.is_paused = True

    def stop(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

    def set_volume(self, val):
        pygame.mixer.music.set_volume(val)

    def get_pos(self):
        return pygame.mixer.music.get_pos() / 1000