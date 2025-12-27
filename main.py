import os
import json
import asyncio
from flask import Flask, request
from pyrogram import Client, filters, types
from pyrogram.errors import AuthKeyUnregistered, FloodWait

# --- [ إعدادات الحساب والبوت ] ---
API_ID = 22498362
API_HASH = "35f421873aebd67dcf4c383e4347fc5d"
BOT_TOKEN = "8375988923:AAHPfCfY2KBsPUPrfXDgh-7EQBKEgg1hmYE"

# إعداد السيرفر (Flask) للعمل مع Render أو Railway
app = Flask(__name__)

# إعداد البوت الرئيسي
bot = Client(
    "mirale_system",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ملفات خزن البيانات
SESSIONS_FILE = "sessions.json"
TASKS_FILE = "tasks.json"

def load_data(f):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as file: return json.load(file)
        except: return {}
    return {}

def save_data(f, data):
    with open(f, "w", encoding="utf-8") as file: json.dump(data, file, indent=4, ensure_ascii=False)

# --- [ أوامر التحكم ] ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid = str(message.from_user.id)
    sessions = load_data(SESSIONS_FILE)
    has_sess = uid in sessions and len(str(sessions[uid])) > 50
    status = "✅ مرتبطة (V2)" if has_sess else "❌ غير مرتبطة"
    
    text = (
        "🚀 **نظام Mirale V6 الاحترافي**\n\n"
        f"⚙️ حالة حسابك: **{status}**\n"
        "📡 النوع: **سحابي (Webhook)**\n"
        "🛡️ الميزة: **كاشف تغيير اليوزر نشط**\n\n"
        "💬 للمراقبة: `حفظ الآيدي يوزر_القناة`"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ربط حساب", callback_data="add"),
         InlineKeyboardButton("🗑️ حذف الحساب", callback_data="del")]
    ])
    await message.reply_text(text, reply_markup=kb)

@bot.on_message(filters.text & filters.private)
async def handle_input(client, message):
    uid = str(message.from_user.id)
    text = message.text.strip()
    sessions = load_data(SESSIONS_FILE)

    # استقبال كود الجلسة
    if sessions.get(uid) == "WAIT":
        if len(text) > 50:
            sessions[uid] = text
            save_data(SESSIONS_FILE, sessions)
            await message.reply_text("✅ تم الربط بنجاح!")
        return

    # حفظ مهمة مراقبة
    if text.startswith("حفظ"):
        try:
            p = text.split()
            tid, ch_input = p[1], p[2].replace("@", "").split("/")[-1]
            
            # استخراج الآيدي الثابت للقناة (ميزة الإعجاز)
            async with Client("temp", session_string=sessions[uid], api_id=API_ID, api_hash=API_HASH, in_memory=True) as temp:
                chat = await temp.get_chat(ch_input)
                real_id = chat.id

            tasks = load_data(TASKS_FILE)
            tasks[tid] = {"owner": uid, "id": real_id, "user": ch_input}
            save_data(TASKS_FILE, tasks)
            await message.reply_text(f"✅ تم البدء! سأراقب `{tid}` في القناة ذات الآيدي: `{real_id}`")
        except Exception as e:
            await message.reply_text(f"⚠️ خطأ: {e}")

# --- [ محرك المغادرة الذكي ] ---

@bot.on_chat_member_updated()
async def auto_leave(client, update):
    if update.old_chat_member and not update.new_chat_member:
        tid = str(update.old_chat_member.user.id)
        tasks = load_data(TASKS_FILE)
        
        if tid in tasks:
            data = tasks[tid]
            sessions = load_data(SESSIONS_FILE)
            oid = data["owner"]
            
            if oid in sessions:
                try:
                    async with Client("worker", session_string=sessions[oid], api_id=API_ID, api_hash=API_HASH, in_memory=True) as u:
                        await u.leave_chat(data["id"])
                    await bot.send_message(oid, f"🚨 **تم صيد غدار!**\nالآيدي `{tid}` غادر، فغادرتُ من قناته (الآيدي: `{data['id']}`) فوراً.")
                except Exception as e:
                    await bot.send_message(oid, f"❌ فشلت المغادرة: {e}")
            
            del tasks[tid]
            save_data(TASKS_FILE, tasks)

# --- [ مسارات السيرفر ] ---

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
async def process_webhook():
    if request.headers.get('content-type') == 'application/json':
        update = await request.get_json()
        await bot.process_update(types.Update.de_json(bot, update))
        return 'OK', 200
    return 'Error', 403

@app.route('/')
def home(): return "Bot is Active on Cloud!", 200

if __name__ == "__main__":
    # تشغيل مزدوج للبوت والسيرفر
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start())
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
