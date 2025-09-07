import yt_dlp, subprocess

vlc_process = None

def send_vlc_command(command: str):
    global vlc_process
    if vlc_process and vlc_process.stdin:
        vlc_process.stdin.write((command + '\n').encode())
        vlc_process.stdin.flush()

def stop_playback():
    send_vlc_command('pause')

def scan_queue(queue: list, queue_condition):
    global vlc_process
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
                '--intf', 'rc',
                '--rc-fake-tty',
                '--no-video',
                stream_url
            ]
            vlc_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            vlc_process.wait()
            vlc_process = None
        except Exception as e:
            print(f"Error playing song: {e}")