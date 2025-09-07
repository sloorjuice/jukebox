import yt_dlp, subprocess

def scan_queue(queue: list, queue_condition):
    while True:
        with queue_condition:
            while not queue:
                queue_condition.wait()
            Song = queue.pop(0)
        print(f"\nPlaying {Song.name}")

        # Use yt-dlp to extract the direct audio URL
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'skip_download': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(Song.url, download=False)
                stream_url = info['url']

            cmd = [
                'vlc',
                '--intf', 'dummy',
                '--play-and-exit',
                '--no-video',
                stream_url
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error playing song: {e}")