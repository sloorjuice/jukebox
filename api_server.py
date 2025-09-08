from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import search_song, add_song_to_queue, queue
from song import Song
from media_scanner import pause_playback, skip_playback
from utils.logger import write_queued_song
import json, os

app = FastAPI()

CURRENT_SONG = os.path.join(os.path.dirname(__file__), "logs", "currently_playing.json")

class song_request(BaseModel):
    prompt: str
    
@app.post("/request_song")
def request_song(song_request: song_request):
    try:
        url, name, duration, author = search_song(song_request.prompt)
        song = Song(name, url, duration, author)
        write_queued_song(song, song_request.prompt)
        add_song_to_queue(song)
        return {"status": "added", "song": name, "author": author}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queue")
def get_queue():
    return [{"name": s.name, "author": s.author, "Duratio": s.duration} for s in queue]

@app.get("/currentlyPlayingSong")
def get_currently_playing():
    try:
        with open(CURRENT_SONG, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pauseToggle")
def pauseToggle():
    try:
        pause_playback()
        return {"status": "toggled pause/play"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/skip")
def skip():
    try:
        skip_playback()
        return {"status": "skipped current song"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



