from pytubefix import Search
from datetime import datetime, timedelta
import time, threading, shutil, sys, subprocess, platform, queue, logging

from src.song import Song
from src.media_scanner import scan_queue, prefetch_audio_urls

song_queue = queue.Queue() # Use a python Queue instead of a list
queue_condition = threading.Condition() 

clean_mode = False

# Set logging config and use logging.info, logging.error, etc instead of print statements
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

# dont skip if no songs in cache

# TODO - current song should be cleared when the program starts, in case the program ended before the currently playing song did.
# TODO - Add a way to request a song with a Youtube URL
# TODO - Add a recently played songs that displays up to the 10 last recently played songs
# TODO - On the frontend add a check next to the song in the queue if its ready to be played


def search_song(search_prompt: str, restricted: bool = False, retries: int = 3, delay: float = 1.0) -> tuple[str, str, int, str]:
    """
    Finds a respective video on youtube and returns the title, link, duration and author.
    Use the retries and delays if your internet connection is poor, defaults should be okay though.
    
    Args:
        search_prompt (str): The search query.
        retries (int): Number of retry attempts on failure.
        delay (float): Delay between retries in seconds.

    Returns:
        tuple: (song_link, song_name, song_duration, song_author)
    """
    if not search_prompt:
        raise ValueError("Search prompt cannot be empty")
    
    if restricted:
        search_prompt = f'{search_prompt} clean'
    attempt = 0
    while attempt < retries:
        try:
            results = Search(search_prompt)
            break
        except Exception as e:
            logging.error(f"Network or search error (attempt {attempt+1}/{retries}): {e}")
            attempt += 1
            if attempt < retries:
                time.sleep(delay)
            else:
                return None, None, None, None
    
    if not results.videos:
        return None, None, None, None
    
    #print("Results for search query:")
    #for video in results.videos:
    #    print(f"Title: {video.title}")
    #    print(f"Url: {video.watch_url}")
    #    print(f'Duration: {video.length} sec')
    #    print('---')
    
    first_video = results.videos[0]
    song_name = first_video.title
    song_link = first_video.watch_url
    song_duration = first_video.length
    song_author = first_video.author
    #song_released = first_video.publish_date
    return song_link, song_name, song_duration, song_author

def add_song_to_queue(song: Song):
    """
    Adds a song to the queue.
    
    Args:
        song (Song): The song to add to queue.
    """
    logging.info(f"[{datetime.now()}] Adding song to queue {song.name} by {song.author} (Duration: {timedelta(seconds=song.duration)})")
    # Moved the queue logger function to the api_server file to also log the search prompt as well
    
    with queue_condition:
        song_queue.put(song) # Use put instead of append for Queue objects
        queue_condition.notify() # Notify the media_scanner that theres a new song in the queue

def is_vlc_installed() -> bool:
    """Checks if VLC is installed and available in PATH."""
    return shutil.which("vlc") is not None

def start_scanner():
    """Starts the Media Scanner which scans the queue and plays the added songs."""
    scan_queue(song_queue, queue_condition)

threading.Thread(target=prefetch_audio_urls, args=(song_queue, queue_condition), daemon=True).start()
scanner_thread = threading.Thread(target=start_scanner, daemon=True)
scanner_thread.start()

if not is_vlc_installed():
    if sys.platform == "darwin":
        cmd = ['brew', 'install', '--cask', 'vlc']
    elif sys.platform.startswith("linux"):
        distro = platform.freedesktop_os_release().get("ID", "") if hasattr(platform, "freedesktop_os_release") else ""
        if distro in ["ubuntu", "debian"]:
            cmd = ['sudo', 'apt', 'install', 'vlc']
        elif distro in ["fedora"]:
            cmd = ['sudo', 'dnf', 'install', 'vlc']
        elif distro in ["centos", "rhel"]:
            cmd = ['sudo', 'yum', 'install', 'vlc']
        elif distro in ["arch", "manjaro"]:
            cmd = ['sudo', 'pacman', '-S', 'vlc']
        else:
            # Fallback: try yay if available, else apt
            if shutil.which("yay"):
                cmd = ['yay', '-S', 'vlc']
            else:
                cmd = ['sudo', 'apt', 'install', 'vlc']
    else:
        logging.error("Unsupported OS. Please install VLC manually.")
        sys.exit(1)
    c = input("VLC is not installed and is essential for this program, would you like to install it? (y/n)")
    if c == "y":
        subprocess.run(cmd, check=True)
else:
    logging.info("Vlc Installed Already.")

if __name__ == "__main__":
    while True:
        song_search_prompt = input("\nSearch for a song > ")
        song_url, song_name, song_duration, song_author = search_song(song_search_prompt, clean_mode)
        song = Song(song_name, song_url, song_duration, song_author)
        add_song_to_queue(song)
        time.sleep(1)  # Wait until the song starts playing