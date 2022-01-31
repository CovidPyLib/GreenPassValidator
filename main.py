import os
from covidpy import CovidPy, InvalidDCC
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

client = Client("gpvalidator", config_file="config.ini")

covid = CovidPy()

mblimit = 2
byteslimit = mblimit * 1024 * 1024 #approximately

@client.on_message(filters.command("start"))
async def start(client, message: Message):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("News", url="https://t.me/GreenPassValidator")], [InlineKeyboardButton("Support", url="https://t.me/CovidPy")]])
    await message.reply_text("Hi, i'm GreenPassValidator, i'm here to help you validate your GreenPass.\n\nYou can send me a photo of your Green Pass and i'll validate it for you.\n\nI'm based on [CovidPy](https://github.com/CovidPyLib/CovidPy) and [Pyrogram](https://github.com/pyrogram/pyrogram), i'm also [open-source](https://github.com/CovidPyLib/GreenPassValidator).", disable_notification=True, parse_mode='markdown')

@client.on_message(filters.photo | filters.document)
async def validate(client: Client, message: Message):
    if message.photo:
        if message.photo.file_size > byteslimit:
            await message.reply_text(f"Sorry, your photo is too big.\n\nMaximum size is {mblimit} MB.")
            return
        photo = message.photo
    elif message.document:
        if message.document.file_size > byteslimit:
            await message.reply_text(f"Sorry, your file is too big.\n\nMaximum size is {mblimit} MB.")
            return
        if not message.document.mime_type.startswith('image/') or message.document.mime_type == 'image/gif':
            await message.reply_text('Sorry, i only accept photos.')
            return
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
        await message.reply_text(
            'Your Green Pass is valid ☑️\nclick on the button below to show more infos',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Show more infos",
                            callback_data=f"infos-{message.message_id}",
                        )
                    ]
                ]
            ),
        )

    else:
        await message.reply_text("Your Green Pass is invalid ❌\nReason: " + "revoked" if data.revoked else "signature isn't valid" + "\nclick on the button below to show more infos", InlineKeyboardMarkup([[InlineKeyboardButton("Show more infos", callback_data=f"infos-{message.message_id}")]]))

@client.on_callback_query()
async def callback(client: Client, query: CallbackQuery):
    if query.data.startswith("infos-"):
        photo = await client.get_messages(query.message.chat.id, int(query.data.split("-")[1]))
        if photo.photo:
            photo = photo.photo
        elif photo.document:
            photo = photo.document
        else:
            await query.answer("Sorry, i can't show you more infos.")
            return
        try:
            p = await client.download_media(photo)
            infos = covid.decode(p)
            cert_type = infos.certificate_type
            cert = None
            if cert_type == "vaccine":
                cert = infos.vaccination_certificate
            elif cert_type == "test":
                cert = infos.test_certificate
            else:
                cert = infos.recovery_certificate
            unique_id = cert[0].certificate_identifier
            mytxt = f"""
Name: ```{infos.owner.first_name}```
Surname: ```{infos.owner.last_name}```
Birthdate: ```{infos.owner.date_of_birth}```
Valid: ```{covid.verify(p).valid}```
Unique identifier: ```{unique_id}```
Certificate type: ```{cert_type}```
            """
            os.remove(p)
            await query.message.edit_text(mytxt)
        except InvalidDCC:
            await query.answer("Sorry, i can't show you more infos.")
            return  
    else:
        await query.answer("Sorry, i can't show you more infos.")


client.run()
