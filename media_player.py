import yt_dlp
import subprocess
from song import Song
import shlex

def play_song(song: Song):
    """Plays a song in a new Terminal window using VLC."""
    print(f"\nPlaying {song.name}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song.url, download=False)
            stream_url = info['url']

        # Use the full path to VLC
        vlc_path = '/Applications/VLC.app/Contents/MacOS/VLC'
        quoted_url = shlex.quote(stream_url)
        vlc_cmd = f'{vlc_path} --intf dummy --play-and-exit --no-video {quoted_url}; exit'

        # Escape for AppleScript
        vlc_cmd_escaped = vlc_cmd.replace('"', '\\"')
        apple_script = f'tell application "Terminal" to do script "{vlc_cmd_escaped}"'
        subprocess.run(['osascript', '-e', apple_script], check=True)
    except Exception as e:
        print(f"Error playing song: {e}")
    return