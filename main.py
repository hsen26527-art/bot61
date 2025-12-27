import os
import json
import asyncio
from flask import Flask, request
from pyrogram import Client, filters, types

API_ID = 22498362
API_HASH = "35f421873aebd67dcf4c383e4347fc5d"
BOT_TOKEN = "8375988923:AAHPfCfY2KBsPUPrfXDgh-7EQBKEgg1hmYE"

app = Flask(__name__)
bot = Client("mirale_cloud", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
async def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = await request.get_json()
        await bot.process_update(types.Update.de_json(bot, update))
        return 'OK', 200
    return 'Error', 400

@app.route('/')
def index(): return "Bot is Online!", 200

if __name__ == "__main__":
    bot.start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

