from utils.logger import write_current_song, write_played_song
import yt_dlp, subprocess, sys, time, logging, concurrent.futures

from song import Song

vlc_process = None  # Variable to represent the actual current vlc process, Essential for doing things like sending commands
audio_url_cache = {}  # Cache for Extracted Audio Urls from the videos
CACHE_SIZE = 5 

# Use yt-dlp to extract the direct audio URL with highest quality settings
ydl_opts = {
    'format': 'bestaudio/best',
    'format_sort': ['acodec:flac', 'acodec:opus', 'acodec:aac', 'abr', 'asr'],
    'quiet': True,
    'skip_download': True,
}

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

def send_vlc_command(command: str):
    """
    Send a command to the current VLC Process.
    See VLC Documentation for possible commands:
    """
    global vlc_process
    if vlc_process and vlc_process.stdin:
        vlc_process.stdin.write((command + '\n').encode())
        vlc_process.stdin.flush()

def pause_playback():
    """
    Sends a pause command to the current VLC Process.
    Pause toggles Pause and Resume, No need for a resume command.
    """
    send_vlc_command('pause')

def skip_playback():
    """Skips the current VLC playback to the next song in the queue."""
    global vlc_process
    if vlc_process and vlc_process.poll() is None:
        send_vlc_command('next')  # Use 'next' to skip to the next in playlist instead of stopping

def prefetch_audio_urls(queue, queue_condition):
    while True:
        with queue_condition:
            # Safely peek at the first CACHE_SIZE items in the queue
            to_prefetch = list(queue.queue)[:CACHE_SIZE]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for song in to_prefetch:
                if song not in audio_url_cache:
                    futures.append(executor.submit(extract_and_cache_url, song))
            concurrent.futures.wait(futures)
        time.sleep(0.5)
                    
def extract_and_cache_url(song):
    try:
        url = extract_audio_url(song)
        audio_url_cache[song] = url
    except Exception as e:
        logging.error(f"Prefetch error for {song.name}: {e}")

def extract_audio_url(song: Song) -> str:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(song.url, download=False)
        stream_url = info['url']
    return stream_url
    
def scan_queue(queue, queue_condition):
    global vlc_process
    while True:
        with queue_condition:
            while queue.empty():
                logging.info("Queue is empty, waiting for songs...")
                queue_condition.wait()
            song_to_play = queue.get()
            write_current_song(song_to_play)
            write_played_song(song_to_play)
        logging.info(f"Playing {song_to_play.name}")

        try:
            # Use cached URL if available
            stream_url = audio_url_cache.pop(song_to_play, None)
            if not stream_url:
                stream_url = extract_audio_url(song_to_play)

            # Choose VLC command based on OS
            if sys.platform.startswith('linux'):
                vlc_cmd = 'cvlc'
            elif sys.platform == 'darwin':
                vlc_cmd = 'vlc'
            else:
                raise Exception("Unsupported OS for VLC playback")

            if vlc_process is None or vlc_process.poll() is not None:
                # Start VLC for the first song or if it crashed
                cmd = [
                    vlc_cmd,
                    '--intf', 'rc',
                    '--no-video',
                    '--audio-time-stretch',            # Enable time stretching for smoother transitions
                    '--audio-filter=compressor:normvol',  # Valid filters for quality
                    '--sout-keep',                     # Keep stream output
                    stream_url
                ]
                vlc_process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,  # Suppress VLC stdout for cleaner logs
                    stderr=subprocess.DEVNULL   # Suppress VLC stderr for cleaner logs
                )
                # Give VLC a moment to start
                time.sleep(1)
            else:
                # Enqueue subsequent songs via RC
                send_vlc_command(f'add {stream_url}')
        except Exception as e:
            logging.error(f"Error playing song: {e}")
            # If error, reset process for next attempt
            if vlc_process:
                vlc_process.terminate()
                vlc_process = None