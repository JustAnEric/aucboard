from pygame.mixer import music
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.aac import AAC
from mutagen.oggflac import OggFLAC
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

import dataclasses, time

@dataclasses.dataclass
class TrackState:
    name: str = "Untitled Track"
    album_name: str = "Untitled Album"
    file_name: str = ""
    duration_s: float = 0.0
    current_time: float = 0.0

class Player:
    def __init__(self):
        self.current_track = TrackState()

    