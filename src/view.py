import discord
import model
import controller


@model.bot.tree.command(name="play", description="Play a song from YouTube")
async def play(interaction: discord.Interaction, song: str):
    await controller.play(interaction, song)


@model.bot.tree.command(name="pause", description="Pause the current song")
async def pause(interaction: discord.Interaction):
    await controller.pause(interaction)


@model.bot.tree.command(
    name="insert", description="Insert a song into the list at a specific index"
)
async def insert(interaction: discord.Interaction, song: str, index: int):
    await controller.insert(interaction, song, index)


@model.bot.tree.command(name="resume", description="Resume the current song")
async def resume(interaction: discord.Interaction):
    await controller.resume(interaction)


@model.bot.tree.command(name="stop", description="Stop all songs")
async def stop(interaction: discord.Interaction):
    await controller.stop(interaction)


@model.bot.tree.command(name="leave", description="Leave the voice channel")
async def leave(interaction: discord.Interaction):
    await controller.leave(interaction)


@model.bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    await controller.skip(interaction)


@model.bot.tree.command(name="list", description="Display the current list")
async def list(interaction: discord.Interaction):
    await controller.list(interaction)


@model.bot.command()
async def sync(ctx: discord.ext.commands.Context):
    await controller.sync(ctx)
