class Song:
    """Simple object to represent songs. Duration is in seconds."""
    def __init__(self, name: str, url: str, duration: int, author: str):
        self.name = name
        self.url = url
        self.duration = duration
        self.author = author