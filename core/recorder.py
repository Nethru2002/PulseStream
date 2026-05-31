import pyaudio
import wave

class AudioRecorder:
    def __init__(self, chunk=1024, sample_format=pyaudio.paInt16, channels=1, rate=44100):
        self.chunk = chunk
        self.sample_format = sample_format
        self.channels = channels
        self.rate = rate
        self.p = pyaudio.PyAudio()

    def record(self, output_filename, seconds=7):
        stream = self.p.open(format=self.sample_format,
                             channels=self.channels,
                             rate=self.rate,
                             frames_per_buffer=self.chunk,
                             input=True)

        frames = []
        for _ in range(0, int(self.rate / self.chunk * seconds)):
            data = stream.read(self.chunk)
            frames.append(data)

        stream.stop_stream()
        stream.close()

        with wave.open(output_filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.sample_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))