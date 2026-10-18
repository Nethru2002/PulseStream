import os
import wave
import pyaudio
from shazamio import Shazam

class SongRecognizer:
    def __init__(self):
        self.shazam = Shazam()
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.record_seconds = 7

    def record_audio(self, filename):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format, channels=self.channels,
                        rate=self.rate, input=True, frames_per_buffer=self.chunk)
        frames = []
        for _ in range(0, int(self.rate / self.chunk * self.record_seconds)):
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))

    async def identify(self, filename):
        return await self.shazam.recognize(filename)