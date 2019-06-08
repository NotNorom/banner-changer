import os
import io
import csv
import random
import asyncio
import aiohttp
import logging
import discord
from discord.ext import tasks, commands
from imgur_downloader import ImgurDownloader

CSV_NAME = "guild-album-mapping.csv"
BOT_TOKEN = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
IMGUR_DOWNLOAD_PATH = "images"

logging.basicConfig(level=logging.INFO)

description = '''An banner changer bot'''
bot = commands.Bot(command_prefix='?', description=description)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='aaaaaaaaaaa'))
    print("logged in: ", bot.user)


@bot.command(description="Set the guild banner image")
async def setbanner(ctx, url: str):
    """Set the guild banner image."""
    if ctx.message.guild is None:
        return

    permissions = ctx.message.author.permissions_in(ctx.channel)
    if not permissions.administrator:
        print("user is not admin")
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send('Could not download file...')
            data = io.BytesIO(await resp.read())
            await ctx.message.guild.edit(banner=data.read())
            ctx.send("Banner set!")


@bot.command(description="Get the guild banner image")
async def getbanner(ctx):
    """Get the guild banner image."""
    if ctx.message.guild is None:
        return
    await ctx.send(ctx.message.guild.banner_url)


@bot.command(description="Set the guild icon")
async def seticon(ctx, url: str):
    """Set the guild icon."""
    if ctx.message.guild is None:
        return

    permissions = ctx.message.author.permissions_in(ctx.channel)
    if not permissions.administrator:
        print("user is not admin")
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send('Could not download file...')
            data = io.BytesIO(await resp.read())
            await ctx.message.guild.edit(icon=data.read())
            await ctx.send("Icon set!")


@bot.command(description="Get the guild icon")
async def geticon(ctx):
    """Get the guild icon."""
    if ctx.message.guild is None:
        return
    await ctx.send(ctx.message.guild.icon_url)


@bot.command(description="Set imgur album/gallery to use images from")
async def setalbum(ctx, url):
    """Set imgur album/gallery and download them"""
    if ctx.message.guild is None:
        return

    permissions = ctx.message.author.permissions_in(ctx.channel)
    if not permissions.administrator:
        print("user is not admin")
        return

    mapping = {}
    # load all mappings into our program
    with open(CSV_NAME, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            # guild.id = imgur link
            if len(row) == 2:
                mapping[int(row[0])] = row[1]

    # replace our current one
    mapping[ctx.message.guild.id] = url
    print("downloaded images:", await download_album_for_guild(ctx.message.guild.id, url))

    # write the new values back to the file
    with open(CSV_NAME, "w", newline='') as f:
        writer = csv.writer(f)
        for key, value in mapping.items():
            writer.writerow([key, value])
    print(mapping)


async def download_album_for_guild(guild_id, url):
    return ImgurDownloader(url, os.path.join(os.path.curdir, IMGUR_DOWNLOAD_PATH), file_name=str(guild_id), delete_dne=True).save_images()


async def set_random_icon_for_guild(guild_id):
    # https://stackoverflow.com/questions/701402/best-way-to-choose-a-random-file-from-a-directory
    image_path = random.choice([f for f in os.listdir(os.path.join(os.path.curdir, IMGUR_DOWNLOAD_PATH, str(guild_id))) if os.path.isfile(os.path.join(os.path.curdir, IMGUR_DOWNLOAD_PATH, str(guild_id), f))])
    image_path = os.path.join(os.path.curdir, IMGUR_DOWNLOAD_PATH, str(guild_id), image_path)
    guild = bot.get_guild(guild_id)
    with open(image_path, 'rb') as data:
        await guild.edit(icon=data.read())


async def set_random_banner_for_guild(guild_id):
    # https://stackoverflow.com/questions/701402/best-way-to-choose-a-random-file-from-a-directory
    image_path = random.choice([f for f in os.listdir(os.path.join(os.path.curdir, IMGUR_DOWNLOAD_PATH, str(guild_id))) if os.path.isfile(os.path.join(os.path.curdir, IMGUR_DOWNLOAD_PATH, str(guild_id), f))])
    image_path = os.path.join(os.path.curdir, IMGUR_DOWNLOAD_PATH, str(guild_id), image_path)
    guild = bot.get_guild(guild_id)
    with open(image_path, 'rb') as data:
        await guild.edit(banner=data.read())


@tasks.loop(hours=24.0)
async def main():
    with open(CSV_NAME, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            await asyncio.sleep(random.randint(0, 10))
            try:
                await set_random_banner_for_guild(int(row[0]))
            except IOError as e:
                guild = bot.get_guild(row[0])
                print(e, guild)


@main.before_loop
async def before_main():
    print("waiting for bot to become ready")
    await bot.wait_until_ready()


main.start()
bot.run(BOT_TOKEN)
