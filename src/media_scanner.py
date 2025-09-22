from src.utils.logger import write_current_song, write_played_song
import yt_dlp, subprocess, sys, time, logging, concurrent.futures

from src.song import Song

vlc_process = None # Variable to represent the actual current vlc process, Essential for doing things like sending commands
audio_url_cache = {} # Cache for Extracted Audio Urls from the videos
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
        send_vlc_command('stop')

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
    
def scan_queue(queue: list, queue_condition):
    global vlc_process
    global currently_playing_song
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

            cmd = [
                vlc_cmd,
                '--intf', 'rc',
                '--no-video',
                '--play-and-exit',
                '--audio-time-stretch',            # Enable time stretching for smoother transitions
                '--audio-filter=compressor:normvol:fadeout:fadein',  # Add fade effects
                '--fadein-time=300',               # 300ms fade in
                '--fadeout-time=300',              # 300ms fade out
                '--fadeout-type=1',                # Linear fade out
                '--fadein-type=1',                 # Linear fade in
                '--compressor-rms-peak=0.2',       # Compressor settings
                '--compressor-attack=20.0',        # Faster attack to catch transients
                '--compressor-release=300.0',      # Slower release for smoother transitions
                '--compressor-threshold=-20.0',    # More aggressive threshold
                '--compressor-ratio=4.0',
                '--compressor-knee=2.0',
                '--compressor-makeup-gain=5.0',    # Slightly reduced makeup gain
                '--norm-max-level=85.0',           # Slightly reduced normalization level
                '--audio-desync=50',               # Small audio buffer to prevent pops
                '--sout-keep',                     # Keep stream output
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
            logging.error(f"Error playing song: {e}")