import os
import io
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyromod import listen
from PIL import Image
from music_tag import load_file
from urllib.parse import quote_plus
import math
import time
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from display_progress import progress_for_pyrogram, humanbytes
import asyncio
import mimetypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")

Bot = Client(
    "Bot",
    bot_token = BOT_TOKEN,
    api_id = API_ID,
    api_hash = API_HASH
)

START_TXT = """
Hi {}, I am Music Editor Bot.
I can change the music tags.
Send a music to get started.

If You Dont want to Change any Item,
just send "/skip" when bot asked for it.
"""

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

@Bot.on_message(filters.command(["start"]))
async def start(bot, update):
    text = START_TXT.format(update.from_user.mention)
    await update.reply_text(text=text)
   
@Bot.on_message(filters.private & (filters.audio | filters.document))
async def tag(bot, m):

    filetype = m.audio or m.document
    
    if not filetype.mime_type.startswith("audio/"):
        if not filetype.file_name:
            await m.reply_text(text=f"Wrong File Type !\n{filetype.mime_type}\n**No filename!**")
            return
        else:
            mt = mimetypes.guess_type(filetype.file_name)[0]
            mt = str(mt)
            if mt and not mt.startswith("audio/"):
                await m.reply_text(text=f"Wrong File Type !\n{mt}\n{filetype.file_name}")
                return
    
    filename = filetype.file_name
    fsize = get_size(filetype.file_size)

    fname = await bot.ask(m.chat.id,f"Enter New Filename: or /skip (no change)\n\n/abort : **Cancel Operation!**\n\nCurrent Name: [{fsize}]\n`{filename}`", filters=filters.text)
    if str(fname.text) == "/abort":
        await bot.send_message(m.chat.id,f"Operation Canceled By User.")
        return
    title = await bot.ask(m.chat.id,f"Enter New Title: or /skip \n\n/abort : **Cancel Operation!**", filters=filters.text)
    if str(title.text) == "/abort":
        await bot.send_message(m.chat.id,f"Operation Canceled By User.")
        return
    artist = await bot.ask(m.chat.id,f"Enter New Artist(s): or /skip \n\n/abort : **Cancel Operation!**", filters=filters.text)
    if str(artist.text) == "/abort":
        await bot.send_message(m.chat.id,f"Operation Canceled By User.")
        return
    
    mes2 = await m.reply_text(
            text=f"**Initiating Download...**",
            quote=True
    )
    try:
        c_time = time.time()
        file_loc = await bot.download_media(
            m,
            progress=progress_for_pyrogram,
            progress_args=(
                f"Downloading Audio [{fsize}] ...",
                mes2,
                c_time
            )
        )
        duration = 0
        metadata = extractMetadata(createParser(file_loc))
        if metadata and metadata.has("duration"):
            duration = metadata.get("duration").seconds
        if fname.text == "/skip":
            fname.text = filename
        if title.text == "/skip":
            if filetype.title:
                title.text = filetype.title
            else:
                title.text = "untitled"
        if artist.text == "/skip":
            if filetype.performer:
                artist.text = filetype.performer
            else:
                artist.text = "unknown artist"
        if artist.text == ".":
            artist.text = "حسن اللهیاری"
    except Exception as e:
        await mes2.edit(f"Download Failed\nError:\n{e}")
        return

    try:
        await mes2.edit("Initiating Upload ...")
        c_time = time.time()
        await bot.send_audio(
            chat_id=m.chat.id,
            file_name=fname.text,
            performer=artist.text,
            title=title.text,
            duration=duration,
            audio=file_loc,
            caption=f"**Filename:** `{fname.text}`\n**Title:** `{title.text}`\n**Artist(s):** `{artist.text}`\n**Size:** {fsize}",
            reply_to_message_id=m.message_id,
            progress=progress_for_pyrogram,
            progress_args=(
                f"Uploading Audio [{fsize}]",
                mes2,
                c_time
            )
         )
        await fname.delete()
        await title.delete()
        await artist.delete()
        await mes2.delete()
        await bot.send_message(m.chat.id,f"Done! Start New Job!")
        os.remove(file_loc)
    except Exception as e:
        await mes2.edit(f"Upload as Audio Failed\nError:\n{e}")
        os.remove(file_loc)
        print(e)
        return

Bot.run()
