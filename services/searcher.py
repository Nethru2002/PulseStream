import yt_dlp
import os

class StreamSearcher:
    def __init__(self):
        self.cache_dir = "cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def download_and_get_path(self, query):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.cache_dir}/%(title)s.%(ext)s',
            'nopart': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'default_search': 'ytsearch1',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            video = info['entries'][0] if 'entries' in info else info
            
            temp_filename = ydl.prepare_filename(video)
            base, _ = os.path.splitext(temp_filename)
            
            return {
                "path": f"{base}.mp3",
                "title": video['title'],
                "thumbnail": video.get('thumbnail'),
                "artist": video.get('uploader', 'Unknown Artist')
            }