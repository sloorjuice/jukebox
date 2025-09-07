from pytubefix import Search

class Song:
    """Simple object to represent songs. Duration is in seconds."""
    def __init__(self, name: str, url:str, duration:int, author:str):
        self.name = name
        self.url = url
        self.duration = duration
        self.author = author

def search_song(search_prompt: str) -> tuple[str, str, int, str]:
    """Takes in a search prompt and finds a respective video on youtube and returns the title, link, duration and author"""
    results = Search(search_prompt)
    #print("Results for search query:")
    #for video in results.videos:
    #    print(f"Title: {video.title}")
    #    print(f"Url: {video.watch_url}")
    #    print(f'Duration: {video.length} sec')
    #    print('---')
    if results.videos:
        first_video = results.videos[0]
        song_name = first_video.title
        song_link = first_video.watch_url
        song_duration = first_video.length
        song_author = first_video.author
        #song_released = first_video.publish_date
    return song_link, song_name, song_duration, song_author

def play_song(song: Song):
    """Plays a song"""
    print(f"\nPlaying {song.name}")
    return

# we need to find out when a song is done playing so we can set playing to false and pop the first item out the queue. 


#queue = []
current_song = None
playing = False
    
while True:
    song_search_prompt = input("\nSearch for a song > ")
    song_url, song_name, song_duration, song_author = search_song(song_search_prompt)
    song = Song(song_name, song_url, song_duration, song_author)
    #queue.append(song)
    if not playing:
        #playing = True # Set playing to false once a song ends
        #play_song(queue[0])
        play_song(song)
    else:
        continue