import os, json, datetime

# TODO - Add error logger to log errors to a file with extensive infomation

# TODO - Add logging to skipped songs, log the song skipped and the next song to play
# TODO - Add logging to paused songs, Log the song that was paused or unpaused

CURRENT_SONG = os.path.join(os.path.dirname(__file__), "..", "logs", "currently_playing.json")
CURRENT_RESTRICTION_MODE = os.path.join(os.path.dirname(__file__), "..", "logs", "current_restriction_mode.json")
ALL_QUEUED_SONGS = os.path.join(os.path.dirname(__file__), "..", "logs", "all_queued_songs.json")
ALL_PLAYED_SONGS = os.path.join(os.path.dirname(__file__), "..", "logs", "all_played_songs.json")

def write_current_song(song):
    os.makedirs(os.path.dirname(CURRENT_SONG), exist_ok=True)
    if song is None:
        data = None
    else:
        data = {
            "name": song.name,
            "author": song.author,
            "duration": song.duration,
            "url": song.url,
            "played_at": datetime.datetime.now().isoformat()
        }
    with open(CURRENT_SONG, "w") as f:
        json.dump(data, f, indent=2)
        
def write_current_restriction_mode(clean: bool = False):
    os.makedirs(os.path.dirname(CURRENT_SONG), exist_ok=True)
    if clean is True:
        data = {
            "clean mode": True
        }
    if clean is False:
        data = {
            "clean mode": False
        }
    with open(CURRENT_SONG, "w") as f:
        json.dump(data, f, indent=2)
        
def write_played_song(song):
    os.makedirs(os.path.dirname(ALL_PLAYED_SONGS), exist_ok=True)
    if song is None:
        return
    data = {
        "name": song.name,
        "author": song.author,
        "duration": song.duration,
        "url": song.url,
        "timestamp": datetime.datetime.now().isoformat()
    }
    # We have to read all the data in the file and and add it before the new song to prevent overwriting
    if os.path.exists(ALL_PLAYED_SONGS):
        with open(ALL_PLAYED_SONGS, "r") as f:
            try:
                songs = json.load(f)
            except Exception:
                songs = []
    else:
        songs = []
    songs.append(data)
    with open(ALL_PLAYED_SONGS, "w") as f:
        json.dump(songs, f, indent=2)

def write_queued_song(song, search_prompt):
    os.makedirs(os.path.dirname(ALL_QUEUED_SONGS), exist_ok=True)
    if song is None:
        return
    data = {
        "name": song.name,
        "author": song.author,
        "duration": song.duration,
        "url": song.url,
        "search_prompt": search_prompt,
        "timestamp": datetime.datetime.now().isoformat()
    }
    # We have to read all the data in the file and and add it before the new song to prevent overwriting
    if os.path.exists(ALL_QUEUED_SONGS):
        with open(ALL_QUEUED_SONGS, "r") as f:
            try:
                songs = json.load(f)
            except Exception:
                songs = []
    else:
        songs = []
    songs.append(data)
    with open(ALL_QUEUED_SONGS, "w") as f:
        json.dump(songs, f, indent=2)
