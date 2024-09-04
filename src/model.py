import gettext
import config
import discord
import logging
from discord.ext import commands
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Song:
    title: str
    channel: str
    original_url: str
    m3u8_url: str


playlist: defaultdict[int, list[Song]] = defaultdict(list)
current_song: defaultdict[int, Song] = defaultdict(Song)

intents = discord.Intents.all()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

translation = gettext.translation(
    config.APP_NAME, localedir=config.LOCALEDIR, languages=[config.LOCALE]
)
_ = translation.gettext

discord.utils.setup_logging(level=logging.INFO, root=True)
