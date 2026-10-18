import pyaudio
import wave

class AudioRecorder:
    def __init__(self, chunk=1024, sample_format=pyaudio.paInt16, channels=1, rate=44100):
        self.chunk = chunk
        self.sample_format = sample_format
        self.channels = channels
        self.rate = rate

    def record(self, output_filename, seconds=7):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.sample_format,
                        channels=self.channels,
                        rate=self.rate,
                        frames_per_buffer=self.chunk,
                        input=True)
        frames = []
        total_chunks = int(self.rate / self.chunk * seconds)
        for _ in range(total_chunks):
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(output_filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(self.sample_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))