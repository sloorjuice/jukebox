from src.utils.logger import write_current_song, write_played_song
import yt_dlp, subprocess, sys, time, logging, concurrent.futures, os, shutil
from collections import OrderedDict
import threading
from typing import Optional

from src.song import Song

vlc_process = None  # Variable to represent the actual current vlc process
logfile_handle = None

# Thread-safe LRU cache for extracted audio URLs
CACHE_SIZE = 5
audio_url_cache = OrderedDict()
cache_lock = threading.Lock()
in_progress_extractions = set()
in_progress_lock = threading.Lock()

current_playing_song = None

# Best-effort yt-dlp options for highest-quality audio extraction
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'skip_download': True,
    'retries': 5,
    'socket_timeout': 20,
    'nocheckcertificate': True,
    'no_warnings': True,
    # prefer IPv4 if some hosts have IPv6 issues
    'source_address': '0.0.0.0',
}

# VLC volume settings (256 == 100% in VLC RC). Clamp to reasonable maximum.
#MAX_VLC_VOLUME = 512  # allow up to 200% if desired; change with caution
MAX_VLC_VOLUME = 384  # 150% volume (256 == 100%)
#MAX_VLC_VOLUME = 256  # 100% volume (do not exceed without care)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)

def send_vlc_command(command: str) -> bool:
    """
    Send a command to the current VLC Process RC interface.
    """
    global vlc_process
    if vlc_process and vlc_process.poll() is None and vlc_process.stdin:
        try:
            vlc_process.stdin.write((command + '\n').encode())
            vlc_process.stdin.flush()
            logging.debug(f"Sent VLC command: {command}")
            return True
        except Exception as e:
            logging.error(f"Failed to send VLC command: {e}")
            return False
    logging.debug("VLC process not available to send command")
    return False

def find_vlc_binary() -> Optional[str]:
    """Return path to VLC binary for current platform, or None if not found."""
    if sys.platform.startswith('linux'):
        return shutil.which("cvlc") or shutil.which("vlc")
    elif sys.platform == 'darwin':
        # Prefer installed CLI wrapper first, then bundle binary
        return shutil.which("vlc") or "/Applications/VLC.app/Contents/MacOS/VLC"
    elif sys.platform.startswith('win'):
        return shutil.which("vlc")
    return None

def ensure_vlc_running() -> bool:
    """Make sure VLC is running and restart it if needed."""
    global vlc_process, logfile_handle

    # If already running and alive, nothing to do
    if vlc_process and vlc_process.poll() is None:
        return True

    vlc_cmd = find_vlc_binary()
    if not vlc_cmd:
        logging.error("VLC binary not found on PATH or expected locations.")
        return False
    if not os.path.exists(vlc_cmd) and not shutil.which(vlc_cmd):
        logging.error(f"VLC binary not accessible: {vlc_cmd}")
        return False

    cmd = [
        vlc_cmd,
        '--intf', 'rc',
        '--no-video',
        '--audio-time-stretch',
        '--audio-filter=compressor:normvol',
        '--gain=2.0',
        '--sout-keep'
    ]

    # Linux: force PulseAudio backend and increase PulseAudio latency to reduce pops
    # (keeps device open longer / reduces underruns when switching streams).
    env = None
    if sys.platform.startswith('linux'):
        cmd.extend(['--aout', 'pulse'])
        env = os.environ.copy()
        env.setdefault('PULSE_LATENCY_MSEC', '60')

    try:
        logging.info(f"Starting VLC process using: {vlc_cmd}")
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        logfile_path = os.path.join(logs_dir, "vlc.log")
        # keep logfile open for lifetime of process
        logfile_handle = open(logfile_path, "ab")
        vlc_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=logfile_handle,
            stderr=logfile_handle,
            env=env
        )
        # Give VLC a moment to initialize
        time.sleep(1.5)
        # Ensure volume at default high level
        set_vlc_volume(MAX_VLC_VOLUME)
        return True
    except Exception as e:
        logging.error(f"Failed to start VLC: {e}")
        return False

def set_vlc_volume(volume: int) -> bool:
    """Clamp and set VLC RC volume (256 == 100%)."""
    vol = max(0, min(int(volume), MAX_VLC_VOLUME))
    if ensure_vlc_running():
        return send_vlc_command(f'volume {vol}')
    return False

def pause_playback():
    if ensure_vlc_running():
        send_vlc_command('pause')
        logging.info("Toggled pause/play")

def skip_playback():
    if ensure_vlc_running():
        send_vlc_command('next')
        logging.info("Skip command sent")

def _cache_put(song: Song, url: str):
    """Insert into LRU cache with eviction."""
    with cache_lock:
        if song in audio_url_cache:
            audio_url_cache.move_to_end(song)
            audio_url_cache[song] = url
        else:
            audio_url_cache[song] = url
            if len(audio_url_cache) > CACHE_SIZE:
                evicted_song, _ = audio_url_cache.popitem(last=False)
                logging.debug(f"Evicted cached URL for: {getattr(evicted_song, 'name', evicted_song)}")

def prefetch_audio_urls(queue, queue_condition):
    """Prefetch audio URLs for upcoming songs in the queue."""
    logging.info("Starting URL prefetch thread")
    while True:
        try:
            with queue_condition:
                to_prefetch = list(queue.queue)[:CACHE_SIZE]

            if to_prefetch:
                logging.debug(f"Prefetching URLs for up to {len(to_prefetch)} songs")
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = []
                    for song in to_prefetch:
                        with cache_lock:
                            cached = song in audio_url_cache
                        with in_progress_lock:
                            already_in_progress = song in in_progress_extractions
                        if not cached and not already_in_progress:
                            with in_progress_lock:
                                in_progress_extractions.add(song)
                            futures.append(executor.submit(_prefetch_worker, song))
                    if futures:
                        concurrent.futures.wait(futures, timeout=30)
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error in prefetch thread: {e}")
            time.sleep(2)

def _prefetch_worker(song: Song):
    try:
        extract_and_cache_url(song)
    finally:
        with in_progress_lock:
            in_progress_extractions.discard(song)

def extract_and_cache_url(song: Song):
    """Extract and cache audio URL for a song (non-blocking callers should use prefetch)."""
    try:
        url = extract_audio_url(song)
        if url:
            _cache_put(song, url)
            logging.info(f"Cached URL for: {song.name}")
        else:
            logging.error(f"Failed to extract URL for: {song.name}")
    except Exception as e:
        logging.error(f"Prefetch error for {song.name}: {e}")

def _choose_best_format(info: dict) -> Optional[str]:
    """
    Given yt-dlp info dict, pick the best audio stream URL available.
    Prefer direct 'url' if present; otherwise inspect 'formats' for highest bitrate audio.
    """
    if not info:
        return None

    # If extractor returns direct URL (single format)
    if 'url' in info and not info.get('is_live', False):
        return info['url']

    # Look into formats
    formats = info.get('formats') or info.get('requested_formats') or []
    if not formats:
        return None

    # Filter audio-only or video formats that have an acodec
    audio_formats = []
    for f in formats:
        # prefer entries with 'acodec' and a 'url'
        if not f.get('url'):
            continue
        acodec = f.get('acodec')
        # If it's audio-only or has an audio codec, consider it.
        if acodec and acodec != 'none':
            audio_formats.append(f)
        else:
            # Some formats don't show acodec but have tbr/abr - still consider
            if f.get('abr') or f.get('tbr'):
                audio_formats.append(f)

    if not audio_formats:
        return None

    # Rank by abr -> tbr -> filesize
    def score(f):
        return (
            float(f.get('abr') or f.get('tbr') or 0.0),
            float(f.get('filesize') or 0)
        )
    best = max(audio_formats, key=score)
    return best.get('url')

def extract_audio_url(song: Song) -> Optional[str]:
    """Extract direct audio URL from a YouTube (or supported) video using yt-dlp."""
    for attempt in range(3):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(song.url, download=False)
                url = _choose_best_format(info)
                if url:
                    logging.info(f"Extracted stream URL for {song.name}")
                    return url
                else:
                    logging.debug(f"No direct stream URL found in info for {song.name}: keys={list(info.keys()) if isinstance(info, dict) else 'N/A'}")
            # small backoff before retry
            time.sleep(1 + attempt)
        except Exception as e:
            logging.error(f"Error extracting URL (attempt {attempt+1}/3) for {song.name}: {e}")
            time.sleep(1 + attempt)
    return None

def scan_queue(queue, queue_condition):
    """Main function that scans the queue and plays songs."""
    global vlc_process, current_playing_song

    logging.info("Starting queue scanner thread")
    while True:
        try:
            # Acquire next song from queue
            with queue_condition:
                while queue.empty():
                    logging.info("Queue is empty, waiting for songs...")
                    queue_condition.wait()
                song_to_play = queue.get()
                write_played_song(song_to_play)

            logging.info(f"Preparing to play: {song_to_play.name}")
            current_playing_song = song_to_play

            if not ensure_vlc_running():
                logging.error("Failed to ensure VLC is running, retrying in 5 seconds")
                time.sleep(5)
                continue

            # Try cache first (use and remove to avoid reuse beyond intended)
            with cache_lock:
                stream_url = audio_url_cache.pop(song_to_play, None)

            if not stream_url:
                logging.info(f"No cached URL for {song_to_play.name}, extracting now...")
                stream_url = extract_audio_url(song_to_play)

            if not stream_url:
                logging.error(f"Failed to get URL for {song_to_play.name}, skipping")
                continue

            logging.info(f"Enqueuing and playing {song_to_play.name}")
            # Enqueue and play the specific URL
            if send_vlc_command(f'enqueue {stream_url}'):
                # ensure playback and loud volume
                send_vlc_command('play')
                set_vlc_volume(MAX_VLC_VOLUME)
                write_current_song(song_to_play, active=True)
                logging.info(f"Now playing: {song_to_play.name}")

                # Wait for the song duration in small intervals so thread remains responsive.
                duration = getattr(song_to_play, "duration", None) or 0
                if duration <= 0:
                    duration = 10  # fallback if missing
                elapsed = 0.0
                poll_interval = 0.5
                while elapsed < duration:
                    time.sleep(poll_interval)
                    elapsed += poll_interval
                write_current_song(None)
            else:
                logging.error(f"Failed to add song to VLC: {song_to_play.name}")

        except Exception as e:
            logging.error(f"Error in queue scanner: {e}")
            # Try to cleanly restart VLC and continue
            try:
                if vlc_process:
                    vlc_process.terminate()
            except Exception:
                pass
            vlc_process = None
            time.sleep(2)