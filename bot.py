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
        await m.reply_text(text=f"Wrong File Type !")
        return
    
    filename = filetype.file_name
    fsize = get_size(filetype.file_size)

    fname = await bot.ask(m.chat.id,f"Enter New Filename: or /skip \n\n Current Name:\n`{filename}` [{fsize}]", filters=filters.text)
    title = await bot.ask(m.chat.id,f"Enter New Title: or /skip", filters=filters.text)
    artist = await bot.ask(m.chat.id,f"Enter New Artist(s): or /skip", filters=filters.text)
    
    c_time = time.time()
    mes2 = await m.reply_text(
            text=f"**Initiating Download...**",
            quote=True
    )
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
            title.text = " "
    if artist.text == "/skip":
        if filetype.performer:
            artist.text = filetype.performer
        else:
            artist.text = " "
    if artist.text == ".":
        artist.text = "حسن اللهیاری"    
    
    await mes2.edit("Initiating Upload ...")
    
    c_time = time.time()    
    try:
        await bot.send_audio(
            chat_id=m.chat.id,
            progress=progress_for_pyrogram,
            progress_args=(
                f"Uploading Audio [{fsize}]",
                mes2,
                c_time
            ),
            file_name=fname.text,
            performer=artist.text,
            title=title.text,
            duration=duration,
            audio=file_loc,
            caption=f"**Filename:** `{fname.text}`\n**Title:** `{title.text}`\n**Artist(s):** `{artist.text}`\n**Size:** {fsize}",
            reply_to_message_id=m.message_id
         )
    except Exception as e:
        await mes2.edit(f"Upload as Audio Failed\nError:\n{e}")
        print(e)

    os.remove(file_loc)
    await fname.delete()
    await title.delete()
    await artist.delete()
    await mes2.delete()
    await bot.send_message(m.chat.id,f"Done! Start New Job!")
        
Bot.run()
