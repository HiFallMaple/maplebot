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
translation = gettext.translation(
    config.APP_NAME, localedir=config.LOCALEDIR, languages=[language_code])
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


async def check_command_in_guild(interaction: discord.Interaction) -> bool:
    """checks if the command is run in a guild"""
    if isinstance(interaction.channel, discord.TextChannel) and interaction.guild is not None:
        return True
    else:
        await interaction.response.send_message(_("Please run this command in a guild"))
        return False


async def join(interaction: discord.Interaction) -> discord.VoiceClient:
    channel = interaction.user.voice.channel
    voice = get(bot.voice_clients, guild=interaction.guild)
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

    return Song(
        title=info["title"],
        channel=info["channel"],
        original_url=info["original_url"],
        m3u8_url=info["url"],
    )


async def play_next(interaction: discord.Interaction, voice: discord.VoiceClient):
    guild_id = interaction.guild.id
    if len(playlist[guild_id]) > 0:
        current_song[guild_id] = playlist[guild_id].pop(0)

        voice.play(
            FFmpegPCMAudio(
                current_song[guild_id].m3u8_url, **config.FFMPEG_OPTIONS),
            after=lambda e: bot.loop.create_task(
                play_next(interaction, voice)),
        )
        await interaction.followup.send(_("Playing the next song in playlist") + f"\n{current_song[guild_id].original_url}")
    else:
        current_song[guild_id] = None
        await interaction.followup.send(_("Completed playing all songs"))


@bot.tree.command(name="play", description="Play a song from YouTube")
async def play(interaction: discord.Interaction, song: str):
    """Play a song from YouTube"""
    if not await check_command_in_guild(interaction):
        return

    guild_id: int = interaction.guild.id

    # Defers the response to avoid interaction timeout
    await interaction.response.defer()

    try:
        voice = await join(interaction)
        song: Song = get_song_metadata(song)

        if voice.is_playing():
            playlist[guild_id].append(song)
            await interaction.followup.send(_("Added to playlist") + f"\n{song.original_url}")
        else:
            current_song[guild_id] = song
            await interaction.followup.send(_("Added to playlist and playing") + f"\n{song.original_url}")
            voice.play(
                FFmpegPCMAudio(song.m3u8_url, **config.FFMPEG_OPTIONS),
                after=lambda e: bot.loop.create_task(
                    play_next(interaction, voice)),
            )
    except Exception as e:
        await interaction.followup.send(_("An error occurred: ") + str(e))


@bot.tree.command(name="pause", description="Pause the current song")
async def pause(interaction: discord.Interaction):
    """Pause the current song"""
    if not await check_command_in_guild(interaction):
        return

    voice = get(bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_playing():
        voice.pause()
        await interaction.response.send_message(_("Paused the current song"))
    else:
        await interaction.response.send_message(_("No song is currently playing"))


@bot.tree.command(name="insert", description="Insert a song into the list at a specific index")
async def insert(interaction: discord.Interaction, song: str, index: int):
    """Insert a song into the list at a specific index"""
    if not await check_command_in_guild(interaction):
        return

    guild_id: int = interaction.guild.id

    await interaction.response.defer()
    url = get_song_metadata(song)

    if index < 0 or index > len(playlist[guild_id]):
        await interaction.followup.send(_("Invalid index"))
        return

    playlist[guild_id].insert(index, url)
    await interaction.followup.send(_("Inserted song into list"))


@bot.tree.command(name="resume", description="Resume the current song")
async def resume(interaction: discord.Interaction):
    """Resume the current song"""
    if not await check_command_in_guild(interaction):
        return

    voice = await join(interaction)
    if voice and voice.is_paused():
        voice.resume()
        await interaction.response.send_message(_("Resumed the current song"))
    else:
        await interaction.response.send_message(_("No song is currently paused"))


@bot.tree.command(name="stop", description="Stop all songs")
async def stop(interaction: discord.Interaction):
    """Stop all songs"""
    if not await check_command_in_guild(interaction):
        return
    voice = await join(interaction)
    playlist[interaction.guild.id].clear()
    voice.stop()
    await interaction.response.send_message(_("Stopped all songs"))


@bot.tree.command(name="leave", description="Leave the voice channel")
async def leave(interaction: discord.Interaction):
    """Leave the voice channel"""
    if not await check_command_in_guild(interaction):
        return

    voice = await join(interaction)
    if voice and voice.is_connected():
        playlist[interaction.guild.id].clear()
        await voice.disconnect()
        await interaction.response.send_message(_("Left the voice channel"))
    else:
        await interaction.response.send_message(_("The bot is not connected to a voice channel"))


@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    """Skip the current song"""
    if not await check_command_in_guild(interaction):
        return
    guild_id: int = interaction.guild.id
    if not current_song[guild_id]:
        await interaction.response.send_message(_("Playlist is empty"))
    await interaction.response.send_message(_("Skip") + f" - [{current_song[guild_id].title}]({current_song[guild_id].original_url})")
    voice = await join(interaction)
    voice.stop()


@bot.tree.command(name="list", description="Display the current list")
async def list(interaction: discord.Interaction):
    """Display the current list"""
    if not await check_command_in_guild(interaction):
        return

    guild_id: int = interaction.guild.id
    if not current_song[guild_id]:
        await interaction.response.send_message(_("Playlist is empty"))
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

    embed.set_footer(
        text=f"{_('Total songs in playlist')}: {len(playlist[guild_id])}")
    await interaction.response.send_message(embed=embed)


@bot.command()
async def sync(ctx: commands.Context):
    sync_result = await bot.tree.sync()
    print(f"Sync result: {sync_result}")
    await ctx.send(_("Synced!"))

if __name__ == "__main__":
    bot.run(config.TOKEN, log_handler=None)
