import sys
import os
# This correctly adds the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
from src.main import add_song_to_queue, song_queue 
from src.song import Song

def test_add_song_to_queue():
    # Verify songs are added in correct order
    test_song = Song("Fake Song", "Fake Url", 120, "Fake Author")
    add_song_to_queue(test_song)
    test_song_from_queue = song_queue.get()  
    assert test_song_from_queue.name == "Fake Song", f"Expected name 'Fake Song', got {test_song_from_queue.name}"
    assert test_song_from_queue.url == "Fake Url", f"Expected URL 'Fake Url', got {test_song_from_queue.url}"
    assert test_song_from_queue.duration == 120, f"Expected duration 120, got {test_song_from_queue.duration}"
    assert test_song_from_queue.author == "Fake Author", f"Expected author 'Fake Author', got {test_song_from_queue.author}"
    
def test_queue_thread_safety():
    # Test concurrent access to queue (multiple API requests)
    raise NotImplementedError
    
def test_queue_persistence_across_restarts():
    # Ensure queue state survives application restarts
    # NOTE - This is not an Implemented feature yet
    raise NotImplementedError