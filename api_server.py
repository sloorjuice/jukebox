from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import search_song, add_song_to_queue, queue
from song import Song
from media_scanner import stop_playback

app = FastAPI()

class song_request(BaseModel):
    prompt: str
    
@app.post("/request_song")
def request_song(song_request: song_request):
    try:
        url, name, duration, author = search_song(song_request.prompt)
        song = Song(name, url, duration, author)
        add_song_to_queue(song)
        return {"status": "added", "song": name, "author": author}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queue")
def get_queue():
    return [{"name": s.name, "author": s.author, "Duratio": s.duration} for s in queue]

@app.post("/stop")
def pause():
    try:
        stop_playback()
        return {"status": "stopped current song"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    