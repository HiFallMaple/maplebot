import yt_dlp
import discord
import config
import model

from model import _
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.utils import get


async def check_command_in_guild(interaction: discord.Interaction) -> bool:
    """checks if the command is run in a guild"""
    if (
        isinstance(interaction.channel, discord.TextChannel)
        and interaction.guild is not None
    ):
        return True
    else:
        await interaction.response.send_message(_("Please run this command in a guild"))
        return False


async def join(interaction: discord.Interaction) -> discord.VoiceClient:
    channel = interaction.user.voice.channel
    voice = get(model.bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
    return voice


def get_song_metadata(song: str) -> model.Song:
    with yt_dlp.YoutubeDL(config.YDL_OPTS) as ydl:
        if "http" in song:  # Check if song is a URL
            info = ydl.extract_info(song, download=False)
        else:
            info = ydl.extract_info(f"ytsearch:{song}", download=False)["entries"][0]

    return model.Song(
        title=info["title"],
        channel=info["channel"],
        original_url=info["original_url"],
        m3u8_url=info["url"],
    )


async def play_next(interaction: discord.Interaction, voice: discord.VoiceClient):
    guild_id = interaction.guild.id
    if len(model.playlist[guild_id]) > 0:
        model.current_song[guild_id] = model.playlist[guild_id].pop(0)

        voice.play(
            FFmpegPCMAudio(
                model.current_song[guild_id].m3u8_url, **config.FFMPEG_OPTIONS
            ),
            after=lambda e: model.bot.loop.create_task(play_next(interaction, voice)),
        )
        await interaction.followup.send(
            _("Playing the next song in playlist")
            + f"\n{model.current_song[guild_id].original_url}"
        )
    else:
        model.current_song[guild_id] = None
        await interaction.followup.send(_("Completed playing all songs"))


async def play(interaction: discord.Interaction, song: str):
    """Play a song from YouTube"""
    if not await check_command_in_guild(interaction):
        return

    guild_id: int = interaction.guild.id

    # Defers the response to avoid interaction timeout
    await interaction.response.defer()

    try:
        voice = await join(interaction)
        song: model.Song = get_song_metadata(song)

        if voice.is_playing():
            model.playlist[guild_id].append(song)
            await interaction.followup.send(
                _("Added to playlist") + f"\n{song.original_url}"
            )
        else:
            model.current_song[guild_id] = song
            await interaction.followup.send(
                _("Added to playlist and playing") + f"\n{song.original_url}"
            )
            voice.play(
                FFmpegPCMAudio(song.m3u8_url, **config.FFMPEG_OPTIONS),
                after=lambda e: model.bot.loop.create_task(
                    play_next(interaction, voice)
                ),
            )
    except Exception as e:
        await interaction.followup.send(_("An error occurred: ") + str(e))


async def pause(interaction: discord.Interaction):
    """Pause the current song"""
    if not await check_command_in_guild(interaction):
        return

    voice = get(model.bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_playing():
        voice.pause()
        await interaction.response.send_message(_("Paused the current song"))
    else:
        await interaction.response.send_message(_("No song is currently playing"))


async def insert(interaction: discord.Interaction, song: str, index: int):
    """Insert a song into the list at a specific index"""
    if not await check_command_in_guild(interaction):
        return

    guild_id: int = interaction.guild.id

    await interaction.response.defer()
    url = get_song_metadata(song)

    if index < 0 or index > len(model.playlist[guild_id]):
        await interaction.followup.send(_("Invalid index"))
        return

    model.playlist[guild_id].insert(index, url)
    await interaction.followup.send(_("Inserted song into list"))


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


async def stop(interaction: discord.Interaction):
    """Stop all songs"""
    if not await check_command_in_guild(interaction):
        return
    voice = await join(interaction)
    model.playlist[interaction.guild.id].clear()
    voice.stop()
    await interaction.response.send_message(_("Stopped all songs"))


async def leave(interaction: discord.Interaction):
    """Leave the voice channel"""
    if not await check_command_in_guild(interaction):
        return

    voice = await join(interaction)
    if voice and voice.is_connected():
        model.playlist[interaction.guild.id].clear()
        await voice.disconnect()
        await interaction.response.send_message(_("Left the voice channel"))
    else:
        await interaction.response.send_message(
            _("The bot is not connected to a voice channel")
        )


async def skip(interaction: discord.Interaction):
    """Skip the current song"""
    if not await check_command_in_guild(interaction):
        return
    guild_id: int = interaction.guild.id
    if not model.current_song[guild_id]:
        await interaction.response.send_message(_("Playlist is empty"))
    await interaction.response.send_message(
        _("Skip")
        + f" - [{model.current_song[guild_id].title}]({model.current_song[guild_id].original_url})"
    )
    voice = await join(interaction)
    voice.stop()


async def list(interaction: discord.Interaction):
    """Display the current list"""
    if not await check_command_in_guild(interaction):
        return

    guild_id: int = interaction.guild.id
    if not model.current_song[guild_id]:
        await interaction.response.send_message(_("Playlist is empty"))
        return
    tmp_str = _("Now playing")
    embed = discord.Embed(
        title=_("Playlist for current guild"),
        description=(
            f'**{tmp_str} - [{model.current_song[guild_id].title}]({model.current_song[guild_id].original_url})**\n\n'
            + "\n".join(
                [
                    f"{i+1}. [{song.title}]({song.original_url})"
                    for i, song in enumerate(model.playlist[guild_id])
                ]
            )
        ),
        color=discord.Color.blue(),
    )
    tmp_str = _("Total songs in playlist")
    embed.set_footer(
        text=f"{tmp_str}: {len(model.playlist[guild_id])}"
    )
    await interaction.response.send_message(embed=embed)


async def sync(ctx: commands.Context):
    sync_result = await model.bot.tree.sync()
    print(f"Sync result: {sync_result}")
    await ctx.send(_("Synced!"))
