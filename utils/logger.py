import os, json

CURRENT_SONG = os.path.join(os.path.dirname(__file__), "..", "logs", "currently_playing.json")

def write_current_song(song):
    os.makedirs(os.path.dirname(CURRENT_SONG), exist_ok=True)
    if song is None:
        data = None
    else:
        data = {
            "name": song.name,
            "author": song.author,
            "duration": song.duration,
            "url": song.url
        }
    with open(CURRENT_SONG, "w") as f:
        json.dump(data, f)