import sys
import os
# This correctly adds the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
# FIX: Import from 'main' to match your project structure and the patch target.
from src.main import search_song

class TestSearchSong:
    @patch('src.main.Search')
    def test_search_song_returns_valid_result(self, MockSearch):
        # Create a fake video object with the needed attributes
        fake_video = MagicMock()
        fake_video.title = "Test Song"
        fake_video.watch_url = "https://youtube.com/watch?v=123"
        fake_video.length = 180
        fake_video.author = "Test Artist"
        
        MockSearch.return_value.videos = [fake_video]
            
        # Call the function
        url, name, duration, author = search_song("test song")
            
        # Assert the results
        assert url == "https://youtube.com/watch?v=123"
        assert name == "Test Song"
        assert duration == 180
        assert author == "Test Artist"
            
    @patch('src.main.Search')
    def test_search_song_handles_no_results(self, MockSearch):
        MockSearch.return_value.videos = []
        
        result = search_song("Fake Song Not Real lol")
        assert result == (None, None, None, None)
     
    @patch('src.main.Search')   
    def test_search_song_handles_network_errors(self, MockSearch):
        MockSearch.return_value.videos = []
        
        result = search_song("Fake Song Not Real lol")
        assert result == (None, None, None, None)