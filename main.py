import os
from covidpy import CovidPy, InvalidDCC
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


client = Client("gpvalidator", config_file="config.ini")

covid = CovidPy()

@client.on_message(filters.command("start"))
async def start(client, message: Message):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("News", url="https://t.me/GreenPassValidator")], [InlineKeyboardButton("Support", url="https://t.me/CovidPy")]])
    await message.reply_text("Hi, i'm GreenPassValidator, i'm here to help you validate your GreenPass.\n\nYou can send me a photo of your Green Pass and i'll validate it for you.\n\nI'm based on [CovidPy](https://github.com/CovidPyLib/CovidPy) and [Pyrogram](https://github.com/pyrogram/pyrogram), i'm also [open-source](https://github.com/CovidPyLib/GreenPassValidator).", disable_notification=True, parse_mode='markdown')

@client.on_message(filters.photo | filters.document)
async def validate(client: Client, message: Message):
    if message.photo:
        photo = message.photo
    elif message.document:
        photo = message.document
    else:
        await message.reply_text("I can't validate this, please send me a photo or a document.")
        return
    try:
        p = await client.download_media(photo)
        data = covid.verify(p)
        os.remove(p)
    except InvalidDCC as e:
        await message.reply_text(f"Sorry, i can't validate this Green Pass.\n{e.details}")
        return
    if data.valid:
        await message.reply_text(f"Your Green Pass is valid ☑️")
    else:
        await message.reply_text("Your Green Pass is invalid ❌\nReason: " + "revoked" if data.revoked else "signature isn't valid")

client.run()