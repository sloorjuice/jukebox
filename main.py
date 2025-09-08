from pytubefix import Search
from song import Song
from media_scanner import scan_queue
import time, threading, shutil, sys, subprocess
from datetime import datetime, timedelta
import platform

queue = []
queue_condition = threading.Condition()

def search_song(search_prompt: str) -> tuple[str, str, int, str]:
    """Takes in a search prompt and finds a respective video on youtube and returns the title, link, duration and author"""
    results = Search(search_prompt)
    #print("Results for search query:")
    #for video in results.videos:
    #    print(f"Title: {video.title}")
    #    print(f"Url: {video.watch_url}")
    #    print(f'Duration: {video.length} sec')
    #    print('---')
    if results.videos:
        first_video = results.videos[0]
        song_name = first_video.title
        song_link = first_video.watch_url
        song_duration = first_video.length
        song_author = first_video.author
        #song_released = first_video.publish_date
    return song_link, song_name, song_duration, song_author

def add_song_to_queue(song: Song):
    """Adds a song to the queue"""
    print(f"[{datetime.now()}] Adding song to queue {song.name} by {song.author} (Duration: {timedelta(seconds=song.duration)})")

    with queue_condition:
        queue.append(song)
        queue_condition.notify()

def is_vlc_installed() -> bool:
    """Checks if VLC is installed and available in PATH."""
    return shutil.which("vlc") is not None

def start_scanner():
    scan_queue(queue, queue_condition)


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
        print("Unsupported OS. Please install VLC manually.")
        sys.exit(1)
    c = input("VLC is not installed and is essential for this program, would you like to install it? (y/n)")
    if c == "y":
        subprocess.run(cmd, check=True)
else:
    print("Vlc Installed Already.")

if __name__ == "__main__":
    while True:
        song_search_prompt = input("\nSearch for a song > ")
        song_url, song_name, song_duration, song_author = search_song(song_search_prompt)
        song = Song(song_name, song_url, song_duration, song_author)
        add_song_to_queue(song)
        time.sleep(1)  # Wait until the song starts playing