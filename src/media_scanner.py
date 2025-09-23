from src.utils.logger import write_current_song, write_played_song
import yt_dlp, subprocess, sys, time, logging, concurrent.futures, os, shutil
from collections import OrderedDict
import threading
from typing import Optional

from src.song import Song

# Global variables
vlc_process = None
logfile_handle = None
current_playing_song = None
song_end_time = None  # Track when current song should end
is_paused = False  # Add pause state tracking

# Thread-safe LRU cache for extracted audio URLs
CACHE_SIZE = 5
audio_url_cache = OrderedDict()
cache_lock = threading.Lock()
in_progress_extractions = set()
in_progress_lock = threading.Lock()

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
MAX_VLC_VOLUME = 384  # 150% volume (256 == 100%)

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

    if vlc_process and vlc_process.poll() is None:
        return True

    if vlc_process:
        try:
            vlc_process.terminate()
            vlc_process.wait(timeout=2)
        except (subprocess.TimeoutExpired, Exception):
            vlc_process.kill()
        vlc_process = None
    
    if logfile_handle and not logfile_handle.closed:
        logfile_handle.close()
        logfile_handle = None

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
        '--rc-fake-tty',
        '--no-video',
        '--audio-time-stretch',
        '--audio-filter=compressor:normvol',
        '--gain=2.0',
        '--sout-keep',
        '--no-loop',           # Disable looping
        '--no-repeat',         # Disable repeat
        '--play-and-exit'      # Exit after playing (but we manage playlist manually)
    ]

    env = None
    if sys.platform.startswith('linux'):
        cmd.extend(['--aout', 'pulse'])
        env = os.environ.copy()
        env.setdefault('PULSE_LATENCY_MSEC', '60')

    try:
        logging.info(f"Starting VLC process using: {vlc_cmd}")
        vlc_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        time.sleep(1.5)
        # Ensure no looping/repeat is enabled
        send_vlc_command('loop off')
        send_vlc_command('repeat off')
        set_vlc_volume(MAX_VLC_VOLUME)
        logging.info("VLC process started successfully.")
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
    global is_paused
    if ensure_vlc_running():
        send_vlc_command('pause')
        is_paused = not is_paused  # Toggle pause state
        # Update the current song with new pause status
        if current_playing_song:
            write_current_song(current_playing_song, active=True, paused=is_paused)
        logging.info(f"Toggled pause/play - now {'paused' if is_paused else 'playing'}")

def skip_playback():
    global current_playing_song, song_end_time, is_paused
    if ensure_vlc_running():
        send_vlc_command('stop')  # Use stop to clear current song
        send_vlc_command('clear')  # Clear the entire playlist
        # Clear current song state immediately
        current_playing_song = None
        song_end_time = None
        is_paused = False  # Reset pause state
        write_current_song(None, active=False, paused=False)
        logging.info("Skipped current song")

def get_pause_status():
    """Get the current pause status."""
    global is_paused
    return is_paused

def get_current_playing_song():
    """Get the currently playing song."""
    global current_playing_song
    return current_playing_song

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
                            futures.append(executor.submit(extract_and_cache_url, song))
                    if futures:
                        concurrent.futures.wait(futures, timeout=30)
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error in prefetch thread: {e}")
            time.sleep(2)

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
    finally:
        with in_progress_lock:
            in_progress_extractions.discard(song)

def _choose_best_format(info: dict) -> Optional[str]:
    """
    Given yt-dlp info dict, pick the best audio stream URL available.
    Prefer direct 'url' if present; otherwise inspect 'formats' for highest bitrate audio.
    """
    if not info:
        return None

    if 'url' in info and not info.get('is_live', False):
        return info['url']

    formats = info.get('formats') or info.get('requested_formats') or []
    if not formats:
        return None

    audio_formats = []
    for f in formats:
        if not f.get('url'):
            continue
        acodec = f.get('acodec')
        if acodec and acodec != 'none':
            audio_formats.append(f)
        else:
            if f.get('abr') or f.get('tbr'):
                audio_formats.append(f)

    if not audio_formats:
        return None

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
            time.sleep(1 + attempt)
        except Exception as e:
            logging.error(f"Error extracting URL (attempt {attempt+1}/3) for {song.name}: {e}")
            time.sleep(1 + attempt)
    return None

def _is_song_finished() -> bool:
    """Check if the current song has finished playing based on duration tracking."""
    global song_end_time, current_playing_song
    
    if not current_playing_song or not song_end_time:
        return True
    
    current_time = time.time()
    return current_time >= song_end_time

def _check_vlc_status() -> str:
    """Check VLC playback status by sending 'status' command and reading response."""
    global vlc_process
    
    if not vlc_process or vlc_process.poll() is not None:
        return "stopped"
    
    try:
        # Send status command
        if send_vlc_command('status'):
            # Try to read some output to check status
            # This is a best-effort approach since VLC RC interface can be inconsistent
            return "unknown"  # We'll rely on duration tracking instead
    except Exception:
        pass
    
    return "unknown"

def scan_queue(queue, queue_condition):
    """Main function that scans the queue and plays songs."""
    global vlc_process, current_playing_song, song_end_time, is_paused

    logging.info("Starting queue scanner thread")
    while True:
        try:
            # Check if current song has finished
            if current_playing_song and _is_song_finished():
                logging.info(f"Song finished: {current_playing_song.name}")
                # Ensure VLC playlist is cleared when song finishes
                if ensure_vlc_running():
                    send_vlc_command('stop')
                    send_vlc_command('clear')
                current_playing_song = None
                song_end_time = None
                is_paused = False  # Reset pause state
                write_current_song(None, active=False, paused=False)
            
            # If a song is currently playing, wait
            if current_playing_song and not _is_song_finished():
                time.sleep(0.5)
                continue
            
            # If no song is playing, check if there's a song in the queue to play
            if queue.empty():
                if current_playing_song is None:
                    write_current_song(None, active=False, paused=False)
                    # Ensure VLC is stopped and cleared when no songs are queued
                    if ensure_vlc_running():
                        send_vlc_command('stop')
                        send_vlc_command('clear')
                time.sleep(1)
                continue

            # Get next song from queue
            with queue_condition:
                song_to_play = queue.get()
            
            logging.info(f"Preparing to play: {song_to_play.name}")

            # Immediately write the song as the next one to play, but not yet active.
            write_current_song(song_to_play, active=False, paused=False)

            if not ensure_vlc_running():
                logging.error("Failed to ensure VLC is running, retrying in 5 seconds")
                # Put the song back in the queue
                with queue_condition:
                    queue.put(song_to_play)
                time.sleep(5)
                continue

            with cache_lock:
                stream_url = audio_url_cache.pop(song_to_play, None)

            if not stream_url:
                logging.info(f"No cached URL for {song_to_play.name}, extracting now...")
                stream_url = extract_audio_url(song_to_play)

            if not stream_url:
                logging.error(f"Failed to get URL for {song_to_play.name}, skipping")
                write_current_song(None, active=False, paused=False)
                continue

            # Clear any existing playlist and add only the new song
            send_vlc_command('clear')
            time.sleep(0.1)  # Small delay to ensure clear command is processed
            
            if send_vlc_command(f'add {stream_url}'):
                # Ensure the song starts playing
                send_vlc_command('play')
                
                # Update state AFTER successfully adding to VLC
                current_playing_song = song_to_play
                song_end_time = time.time() + song_to_play.duration + 3  # Add 3 second buffer
                is_paused = False  # Song starts playing, not paused
                
                # Log the song as played and update the current song to be active
                write_played_song(song_to_play)
                write_current_song(song_to_play, active=True, paused=False)
                
                set_vlc_volume(MAX_VLC_VOLUME)
                logging.info(f"Now playing: {song_to_play.name}")
            else:
                logging.error(f"Failed to add song to VLC: {song_to_play.name}")
                write_current_song(None, active=False, paused=False)

        except Exception as e:
            logging.error(f"Error in queue scanner: {e}")
            try:
                if vlc_process:
                    vlc_process.terminate()
            except Exception:
                pass
            vlc_process = None
            current_playing_song = None
            song_end_time = None
            is_paused = False  # Reset pause state on error
            time.sleep(2)
