class Song:
    """Simple object to represent songs. Duration is in seconds."""
    def __init__(self, name: str, url: str, duration: int, author: str):
        self.name = name
        self.url = url
        self.duration = duration
        self.author = author

    def __eq__(self, other):
        return isinstance(other, Song) and self.url == other.url

    def __hash__(self):
        return hash(self.url)