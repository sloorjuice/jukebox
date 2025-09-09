import sys, os, unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add project root to path (similar to other test files)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api_server import app  # Import the FastAPI app
from src.song import Song

class TestAPIServer(unittest.TestCase):
    def setUp(self):
        """ Create a TestClient for the FastAPI app """
        self.client = TestClient(app)
        # Mock Dependencies to isolate the test
        self.mock_search_song = patch('src.api_server.search_song').start()
        self.mock_add_song_to_queue = patch('src.api_server.add_song_to_queue').start()
        self.mock_write_queued_song = patch('src.api_server.write_queued_song').start()
        
        # Configure mocks with fake data
        self.mock_search_song.return_value = ("https://fakeurl.com", "Fake Song", 120, "Fake Author")
        self.mock_add_song_to_queue.return_value = None
        self.mock_write_queued_song.return_value = None
        
    def tearDown(self):
        """ Stop patches after each test """
        patch.stopall()
    
    def test_request_song_valid_input(self):
        """ Test successful song request with valid input"""
        valid_payload = {"prompt": "test song"}
        
        # Send POST request to /request_song
        response = self.client.post("/request_song", json=valid_payload)
        
        # Assert response status and content
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["status"], "added")
        self.assertEqual(response_data["song"], "Fake Song")
        self.assertEqual(response_data["author"], "Fake Author")
        
        # Assert mocks were called with expected arguments
        self.mock_search_song.assert_called_once_with("test song")
        self.mock_add_song_to_queue.assert_called_once()
        self.mock_write_queued_song.assert_called_once()
        
        # Verify the Song object was created correctly (check the call to add_song_to_queue)
        called_args = self.mock_add_song_to_queue.call_args[0][0]  # Get the Song argument
        self.assertIsInstance(called_args, Song)
        self.assertEqual(called_args.name, "Fake Song")
        self.assertEqual(called_args.url, "https://fakeurl.com")
        self.assertEqual(called_args.duration, 120)
        self.assertEqual(called_args.author, "Fake Author")
        
    def test_request_song_invalid_input(self):
        # Test error handling for bad requests
        raise NotImplementedError
        
    def test_queue_endpoint_returns_current_state(self):
        # Verify queue endpoint accuracy
        raise NotImplementedError
        
    def test_concurrent_api_requests(self):
        # Test multiple simultaneous song requests
        raise NotImplementedError