from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import json, os
import socket

from src.main import add_song_to_queue, set_clean_mode, get_clean_mode
from src.media_scanner import pause_playback, skip_playback
from src.utils.logger import write_queued_song, write_current_restriction_mode
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP

local_ip = get_local_ip()
hostname = socket.gethostname()
local_hostname_local = f"{hostname}.local"
local_hostname_lan = f"{hostname}.lan"

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    f"http://{local_ip}:3000",
    f"http://{local_hostname_local}:3000",
    f"http://{local_hostname_lan}:3000",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("CORS allowed_origins:", allowed_origins)

def get_current_song_path():
    return os.path.join(os.path.dirname(__file__), "logs", "currently_playing.json")

def get_queue_path():
    return os.path.join(os.path.dirname(__file__), "logs", "all_queued_songs.json")

class SongRequest(BaseModel):
    prompt: str

class ToggleCleanModeRequest(BaseModel):
    prompt: bool

class SongResponse(BaseModel):
    status: str
    song: str
    author: str

class ToggleRestrictionResponse(BaseModel):
    status: str
    clean_mode: bool

class QueueSong(BaseModel):
    name: str
    author: str
    duration: int
    active: bool # To indicate if the song is waiting to be played or already playing
    search_prompt: str
    url: str

class CurrentlyPlayingResponse(BaseModel):
    name: Optional[str]
    author: Optional[str]
    duration: Optional[int]
    url: Optional[str]
    played_at: Optional[str]
    active: bool

@app.post("/request_song", response_model=SongResponse)
def request_song(song_request: SongRequest):
    # This part of the code is fine, no changes needed
    from src.main import search_song, Song # Importing here to avoid circular dependencies
    clean_mode = get_clean_mode()
    url, name, duration, author = search_song(song_request.prompt, restricted=clean_mode)
    if not url:
        raise HTTPException(status_code=404, detail="Song not found")
    song = Song(name, url, duration, author)
    add_song_to_queue(song, song_request.prompt)
    return {"status": "added", "song": name, "author": author}

@app.post("/toggle_clean_mode", response_model=ToggleRestrictionResponse)
def toggle_clean_mode(toggle_clean_mode_request: ToggleCleanModeRequest):
    write_current_restriction_mode(toggle_clean_mode_request.prompt)
    set_clean_mode(toggle_clean_mode_request.prompt)
    return {"status": "Toggled", "clean_mode": toggle_clean_mode_request.prompt}

@app.get("/queue", response_model=list[QueueSong])
def get_queue(queue_path: str = Depends(get_queue_path)):
    try:
        with open(queue_path, "r") as f:
            data = json.load(f)
        return [QueueSong(**item) for item in data]
    except FileNotFoundError:
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading queue file: {e}")

@app.get("/currentlyPlayingSong", response_model=CurrentlyPlayingResponse)
def get_currently_playing(current_song_path: str = Depends(get_current_song_path)):
    try:
        with open(current_song_path, "r") as f:
            data = json.load(f)
            # Handle the case where the file is empty or contains 'null'
            if data is None:
                return {"name": None, "author": None, "duration": None, "url": None, "played_at": None, "active": False}
        return CurrentlyPlayingResponse(**data)
    except (FileNotFoundError, json.JSONDecodeError):
        # File doesn't exist or is empty/invalid JSON, means nothing is playing
        return {"name": None, "author": None, "duration": None, "url": None, "played_at": None, "active": False}
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
