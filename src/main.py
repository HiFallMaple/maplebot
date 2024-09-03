import yt_dlp
import discord
import config
import gettext
import logging

from dataclasses import dataclass
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.utils import get
from collections import defaultdict


discord.utils.setup_logging(level=logging.INFO, root=True)
logger = logging.getLogger(__name__)

# setup i18n
language_code = config.LOCALE
logger.info(f"Language code: {language_code}")
translation = gettext.translation(config.APP_NAME, localedir=config.LOCALEDIR, languages=[language_code])
global _
_ = translation.gettext


@dataclass
class Song:
    title: str
    channel: str
    original_url: str
    m3u8_url: str


global playlist
playlist: defaultdict[int, list[Song]] = defaultdict(list)
global current_song
current_song: defaultdict[int, Song] = defaultdict(Song)

intents = discord.Intents.all()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def check_command_in_guild(ctx: discord.Interaction) -> bool:
    """checks if the command is run in a guild"""
    if isinstance(ctx.channel, discord.TextChannel) and ctx.guild is not None:
        return True
    else:
        await ctx.send(_("Please run this command in a guild"))
        return False


async def join(ctx: discord.Interaction) -> discord.VoiceClient:
    channel = ctx.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
    return voice


def get_song_metadata(song: str) -> Song:
    with yt_dlp.YoutubeDL(config.YDL_OPTS) as ydl:
        if "http" in song:  # Check if song is a URL
            info = ydl.extract_info(song, download=False)
        else:
            info = ydl.extract_info(f"ytsearch:{song}", download=False)["entries"][0]
    with open("info.json", "w") as f:
        import json

        f.write(json.dumps(info, indent=4))
    return Song(
        title=info["title"],
        channel=info["channel"],
        original_url=info["original_url"],
        m3u8_url=info["url"],
    )


async def play_next(ctx: discord.Interaction, voice: discord.VoiceClient):
    guild_id = ctx.guild.id
    if len(playlist[guild_id]) > 0:
        current_song[guild_id] = playlist[guild_id].pop()
        print(f"Playing next song: {current_song[guild_id]}")

        voice.play(
            FFmpegPCMAudio(current_song[guild_id].m3u8_url, **config.FFMPEG_OPTIONS),
            after=lambda e: bot.loop.create_task(play_next(ctx, voice)),
        )
        await ctx.send(_("Playing the next song in playlist")+f"\n{current_song[guild_id].original_url}")
    else:
        current_song[guild_id] = None
        await ctx.send(_("Completed playing all songs"))


@bot.hybrid_command()
async def play(ctx: discord.Interaction, song: str):
    """Play a song from YouTube"""
    if not await check_command_in_guild(ctx):
        return

    guild_id: int = ctx.guild.id

    await ctx.defer()
    voice = await join(ctx)
    print(f"{voice}, {type(voice)}")
    song: Song = get_song_metadata(song)

    if voice.is_playing():
        playlist[guild_id].append(song)
        await ctx.send(_("Added to playlist")+f"\n{song.original_url}")
    else:
        current_song[guild_id] = song
        await ctx.send(_("Added to playlist and playing")+f"\n{song.original_url}")
        voice.play(
            FFmpegPCMAudio(song.m3u8_url, **config.FFMPEG_OPTIONS),
            after=lambda e: bot.loop.create_task(play_next(ctx, voice)),
        )


@bot.hybrid_command()
async def pause(ctx: discord.Interaction):
    """Pause the current song"""
    if not await check_command_in_guild(ctx):
        return

    voice = await join(ctx)
    if voice and voice.is_playing():
        voice.pause()
    else:
        await ctx.send(_("No song is currently playing"))


@bot.hybrid_command()
async def insert(ctx: discord.Interaction, song: str, index: int):
    """Insert a song into the list at a specific index"""
    if not await check_command_in_guild(ctx):
        return

    guild_id: int = ctx.guild.id

    await ctx.defer()
    url = get_song_metadata(song)

    if index < 0 or index > len(playlist[guild_id]):
        await ctx.send(_("Invalid index"))
        return

    playlist[guild_id].insert(index, url)
    await ctx.send(_("Inserted song into list"))


@bot.hybrid_command()
async def resume(ctx: discord.Interaction):
    """Resume the current song"""
    if not await check_command_in_guild(ctx):
        return

    voice = await join(ctx)
    if voice and voice.is_paused():
        voice.resume()
    else:
        await ctx.send(_("No song is currently paused"))


@bot.hybrid_command()
async def stop(ctx: discord.Interaction):
    """Stop all songs"""
    if not await check_command_in_guild(ctx):
        return
    voice = await join(ctx)
    playlist[ctx.guild.id].clear()
    voice.stop()


@bot.hybrid_command()
async def leave(ctx: discord.Interaction):
    """Leave the voice channel"""
    if not await check_command_in_guild(ctx):
        return

    voice = await join(ctx)
    if voice and voice.is_connected():
        playlist[ctx.guild.id].clear()
        await voice.disconnect()
    else:
        await ctx.send(_("The bot is not connected to a voice channel"))


@bot.hybrid_command()
async def skip(ctx: discord.Interaction):
    """Skip the current song"""
    if not await check_command_in_guild(ctx):
        return

    voice = await join(ctx)
    voice.stop()
    await play_next(ctx, voice)


@bot.hybrid_command()
async def list(ctx: discord.Interaction):
    """Display the current list"""
    if not await check_command_in_guild(ctx):
        return

    guild_id: int = ctx.guild.id
    if not current_song[guild_id]:
        await ctx.send(_("Playlist is empty"))
        return

    embed = discord.Embed(
        title=_("Playlist for current guild"),
        description=(
            f"**{_('Now playing')} - [{current_song[guild_id].title}]({current_song[guild_id].original_url})**\n\n"
            + "\n".join(
                [
                    f"{i+1}. [{song.title}]({song.original_url})"
                    for i, song in enumerate(playlist[guild_id])
                ]
            )
        ),
        color=discord.Color.blue(),
    )

    embed.set_footer(text=f"{_('Total songs in playlist')}: {len(playlist[guild_id])}")
    await ctx.send(embed=embed)


@bot.command()
async def sync(ctx: discord.Interaction):
    sync_result = await bot.tree.sync()
    print(f"Sync result: {sync_result}")
    print(discord.Object(id=ctx.guild.id))
    await ctx.send(_("Synced!"))

if __name__ == "__main__":
    bot.run(config.TOKEN, log_handler=None)
