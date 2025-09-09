# SLOORJUKE (a jukebox by sloorjuice)

A Python-powered CLI and API for music streaming that allows you to search for YouTube videos, queue songs, and play them using VLC media player. The application features a FastAPI REST API for remote control and management, intended to be used on a Raspberry Pi (or alternative) with speakers to make a home jukebox that can be controlled by any device in your household. You could even complete it with port forwarding to use the device from anywhere.

## Features

- 🎵 **YouTube Search Integration**: Search and queue songs directly from YouTube
- 🎛️ **REST API**: Control playback remotely via HTTP endpoints
- 📱 **Queue Management**: Add, view, and manage your music queue
- ⏯️ **Playback Controls**: Play, pause, and skip functionality
- 📊 **Logging System**: Tracks played and queued songs with timestamps
- 🚀 **Audio Prefetching**: Intelligent caching for smoother playback
- 🎧 **VLC Integration**: Uses VLC media player for reliable audio playback straight in the terminal, no VLC window or anything

### Coming Soon

- 🖥️ **Frontend Template**: Easily set up and host a website with your server to control the API
- 📄 **Setup Guide**: A setup guide to help anyone spin up this project to use in their home, experienced or not

## Prerequisites

- **Python 3.7+**
- **VLC Media Player** (automatically installed if missing)

### Supported Operating Systems
- macOS
- Linux

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/sloorjuice/jukebox/
cd jukebox
```

2. **Create and activate a virtual environment** (recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
```

3. **Install Python dependencies**
Use the recommended script
```bash
# Make the script executable
chmod +x scripts/install.sh

# Start the API server using the script
./scripts/install.sh
```

1. **VLC Installation** (if not already installed)
The application will automatically detect if VLC is missing and offer to install it:
- **macOS**: Uses Homebrew (`brew install --cask vlc`)
- **Linux**: Uses system package manager (apt, dnf, yum, pacman)

## Usage

### Running the Application

#### Method 1: API Server Mode
Start the FastAPI server with the recommended script to control the application remotely:

```bash
# Make the script executable
chmod +x scripts/start_server.sh

# Start the API server using the script
./scripts/start_server.sh
```

The API will be available at `http://localhost:8000` or `http://your-ip:8000`

#### Method 2: Command Line Mode
Run the application interactively:

```bash
python src/main.py
```

### API Endpoints

#### POST `/request_song`
Add a song to the queue by search prompt.

**Request Body:**
```json
{
  "prompt": "song name or search query"
}
```

**Response:**
```json
{
  "status": "added",
  "song": "Song Title",
  "author": "Artist Name"
}
```

#### GET `/queue`
Get the current song queue.

**Response:**
```json
[
  {
    "name": "Song Title",
    "author": "Artist Name",
    "duration": 240
  }
]
```

#### GET `/currentlyPlayingSong`
Get information about the currently playing song.

**Response:**
```json
{
  "name": "Song Title",
  "author": "Artist Name",
  "duration": 240,
  "url": "https://youtube.com/watch?v=...",
  "played_at": "2024-01-01T12:00:00"
}
```

#### POST `/pauseToggle`
Toggle pause/play for the current song.

**Response:**
```json
{
  "status": "toggled pause/play"
}
```

#### POST `/skip`
Skip the currently playing song.

**Response:**
```json
{
  "status": "skipped current song"
}
```

### API Documentation
Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Architecture

### Core Components

- **`main.py`**: Entry point, song search functionality, and queue management
- **`api_server.py`**: FastAPI REST API endpoints
- **`media_scanner.py`**: Audio URL extraction, caching, and VLC playback control
- **`song.py`**: Song data model
- **`utils/logger.py`**: Logging system for tracking songs and playback history

### Key Features

#### Smart Audio Caching
The application prefetches audio URLs for the next 5 songs in the queue, ensuring smooth playback transitions.

#### Comprehensive Logging
Three types of logs are maintained:
- **Currently Playing**: Real-time status of active song
- **Queue History**: All songs added to the queue with search prompts
- **Playback History**: Complete log of played songs with timestamps

#### Cross-Platform VLC Integration
Automatically detects the operating system and uses the appropriate VLC command (`cvlc` for Linux, `vlc` for macOS).

## Configuration

### Log Files Location
All logs are stored in the `logs/` directory:
- `currently_playing.json`: Current song status
- `all_queued_songs.json`: Complete queue history
- `all_played_songs.json`: Complete playback history

### Dependencies
- **pytubefix**: YouTube search and metadata extraction
- **yt-dlp**: Audio stream URL extraction
- **fastapi**: REST API framework
- **uvicorn**: ASGI server
- **pydantic**: Data validation

## Troubleshooting

### VLC Not Found
If you encounter VLC-related errors:
1. Ensure VLC is installed and available in your system PATH
2. On Linux, try installing with your distribution's package manager
3. On macOS, install via Homebrew: `brew install --cask vlc`

### YouTube Access Issues
If YouTube videos fail to load:
- Check your internet connection
- Some videos may be region-restricted or have playback limitations
- The application will log errors for debugging

### Permission Errors
If you encounter permission errors with log files:
```bash
mkdir logs
chmod 755 logs
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

[contact@sloor.dev](mailto:contact@sloor.dev)
