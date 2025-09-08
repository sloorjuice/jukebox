from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from main import search_song, add_song_to_queue, song_queue
from song import Song
from media_scanner import pause_playback, skip_playback
from utils.logger import write_queued_song
import json, os

app = FastAPI()

def get_current_song_path():
    return os.path.join(os.path.dirname(__file__), "logs", "currently_playing.json")

class SongRequest(BaseModel):
    prompt: str

class SongResponse(BaseModel):
    status: str
    song: str
    author: str

class QueueSong(BaseModel):
    name: str
    author: str
    duration: int

@app.post("/request_song", response_model=SongResponse)
def request_song(song_request: SongRequest):
    url, name, duration, author = search_song(song_request.prompt)
    song = Song(name, url, duration, author)
    write_queued_song(song, song_request.prompt)
    add_song_to_queue(song)
    return {"status": "added", "song": name, "author": author}

@app.get("/queue", response_model=list[QueueSong])
def get_queue():
    return [QueueSong(name=s.name, author=s.author, duration=s.duration) for s in song_queue]

@app.get("/currentlyPlayingSong")
def get_currently_playing(current_song_path: str = Depends(get_current_song_path)):
    try:
        with open(current_song_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pauseToggle")
def pause_toggle():
    pause_playback()
    return {"status": "toggled pause/play"}

@app.post("/skip")
def skip():
    skip_playback()
    return {"status": "skipped current song"}



