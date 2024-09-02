import os

APP_NAME = 'maplebot'
LOCALEDIR='../locales'

TOKEN = os.getenv('DISCORD_TOKEN')
MAX_PLAYLIST_SIZE = os.getenv('MAX_PLAYLIST_SIZE')
LOCALE = os.getenv('LOCALE')
DEFAULT_VOLUME = os.getenv('DEFAULT_VOLUME')
STAY_TIME = os.getenv('STAY_TIME')

YDL_OPTS = {
    "format": "bestaudio/best",
    "skip_download": True,
    "force_generic_extractor": True,
    "noplaylist": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "ffmpeg_location": "../bin/ffmpeg",
}
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
    "executable": "../bin/ffmpeg",
}
