import os
import json
import asyncio
from flask import Flask, request
from pyrogram import Client, filters, types
from pyrogram.errors import AuthKeyUnregistered

# --- [ الإعدادات الأساسية ] ---
API_ID = 22498362
API_HASH = "35f421873aebd67dcf4c383e4347fc5d"
BOT_TOKEN = "8375988923:AAHPfCfY2KBsPUPrfXDgh-7EQBKEgg1hmYE"

# إعداد تطبيق الويب (Flask)
app = Flask(__name__)

# إعداد بوت التليجرام
bot = Client(
    "mirale_cloud_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=None # لضمان عدم تداخل الملفات
)

# ملفات تخزين البيانات (سيتم إنشاؤها تلقائياً على السيرفر)
SESSIONS_FILE = "sessions.json"
TASKS_FILE = "tasks.json"

def load_data(f):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as file:
                return json.load(file)
        except: return {}
    return {}

def save_data(f, data):
    with open(f, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# --- [ واجهة التحكم - الأوامر ] ---

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    uid = str(message.from_user.id)
    sessions = load_data(SESSIONS_FILE)
    has_sess = uid in sessions and len(str(sessions[uid])) > 50
    status = "✅ مرتبطة (V2)" if has_sess else "❌ غير مرتبطة"
    
    text = (
        "🚀 **مرحباً بك في بوت الحماية السحابي (Mirale V6)**\n\n"
        f"⚙️ حالة حسابك: **{status}**\n"
        "📡 النظام: **Webhook (يعمل 24 ساعة)**\n\n"
        "💬 للمراقبة أرسل: `حفظ الآيدي يوزر_القناة`"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ربط حساب (V2)", callback_data="add_sess"),
         InlineKeyboardButton("🗑️ حذف الحساب", callback_data="del_sess")]
    ])
    await message.reply_text(text, reply_markup=buttons)

@bot.on_message(filters.text & filters.private)
async def text_logic(client, message):
    uid = str(message.from_user.id)
    text = message.text.strip()
    sessions = load_data(SESSIONS_FILE)

    # استقبال كود الـ Session
    if sessions.get(uid) == "WAITING_CODE":
        if len(text) > 60:
            sessions[uid] = text
            save_data(SESSIONS_FILE, sessions)
            await message.reply_text("✅ تم ربط الحساب بنجاح في السيرفر!")
        else:
            await message.reply_text("⚠️ الكود غير صحيح، يرجى إرسال كود V2 كامل.")
        return

    # حفظ مهمة مراقبة جديدة
    if text.startswith("حفظ"):
        try:
            parts = text.split()
            target_id = parts[1]
            channel_input = parts[2].replace("@", "").split("/")[-1]
            
            # جلب الآيدي الثابت للقناة (كاشف التغيير)
            async with Client("temp", session_string=sessions[uid], api_id=API_ID, api_hash=API_HASH, in_memory=True) as temp_app:
                chat = await temp_app.get_chat(channel_input)
                real_chat_id = chat.id

            tasks = load_data(TASKS_FILE)
            tasks[target_id] = {"owner": uid, "chat_id": real_chat_id, "username": channel_input}
            save_data(TASKS_FILE, tasks)
            await message.reply_text(f"✅ تمت إضافة المراقبة بنجاح!\n🆔 الآيدي الثابت: `{real_chat_id}`")
        except Exception as e:
            await message.reply_text(f"❌ خطأ في الحفظ: تأكد من ربط حسابك وصحة اليوزر.\n`{e}`")

# --- [ كاشف الغدر والمغادرة التلقائية ] ---

@bot.on_chat_member_updated()
async def on_leave(client, update):
    if update.old_chat_member and not update.new_chat_member:
        user_id = str(update.old_chat_member.user.id)
        tasks = load_data(TASKS_FILE)
        
        if user_id in tasks:
            task = tasks[user_id]
            sessions = load_data(SESSIONS_FILE)
            owner_id = task["owner"]
            
            if owner_id in sessions:
                try:
                    async with Client("worker", session_string=sessions[owner_id], api_id=API_ID, api_hash=API_HASH, in_memory=True) as user_app:
                        await user_app.leave_chat(task["chat_id"])
                    await bot.send_message(owner_id, f"🚨 **صيد غدار!**\nالشخص `{user_id}` غادر، وتمت المغادرة من قناته @{task['username']} فوراً.")
                except Exception as e:
                    await bot.send_message(owner_id, f"⚠️ فشلت المغادرة التلقائية: `{e}`")
            
            del tasks[user_id]
            save_data(TASKS_FILE, tasks)

# --- [ مسارات Webhook للسيرفر ] ---

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
async def telegram_update():
    if request.headers.get('content-type') == 'application/json':
        data = await request.get_json()
        update = types.Update.de_json(bot, data)
        await bot.process_update(update)
        return 'OK', 200
    return 'Forbidden', 403

@app.route('/')
def home():
    return "Mirale Bot is Running 24/7 on Cloud!", 200

# تشغيل النظام المزدوج
if __name__ == "__main__":
    # تشغيل البوت في الخلفية والسيرفر لاستقبال الطلبات
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start())
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
