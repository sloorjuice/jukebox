import yt_dlp, subprocess, sys
from utils.logger import write_current_song

vlc_process = None



def send_vlc_command(command: str):
    global vlc_process
    if vlc_process and vlc_process.stdin:
        vlc_process.stdin.write((command + '\n').encode())
        vlc_process.stdin.flush()

def pause_playback():
    send_vlc_command('pause')

def skip_playback():
    """Skips the current VLC playback."""
    global vlc_process
    if vlc_process and vlc_process.poll() is None:
        send_vlc_command('stop')

def scan_queue(queue: list, queue_condition):
    global vlc_process
    global currently_playing_song
    while True:
        with queue_condition:
            while not queue:
                queue_condition.wait()
            Song = queue.pop(0)
            write_current_song(Song)
        print(f"\nPlaying {Song.name}")

        # Use yt-dlp to extract the direct audio URL
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'skip_download': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(Song.url, download=False)
                stream_url = info['url']

            # Choose VLC command based on OS
            if sys.platform.startswith('linux'):
                vlc_cmd = 'cvlc'
            elif sys.platform == 'darwin':
                vlc_cmd = 'vlc'
            else:
                raise Exception("Unsupported OS for VLC playback")

            cmd = [
                vlc_cmd,
                '--intf', 'rc',
                '--no-video',
                '--play-and-exit', 
                stream_url
            ]
            vlc_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                # stdout=subprocess.DEVNULL,
                # stderr=subprocess.DEVNULL
            )
            vlc_process.wait()
            vlc_process = None
            write_current_song(None)
        except Exception as e:
            print(f"Error playing song: {e}")