import telebot
import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from supabase import create_client
from pyrogram import Client, filters
from datetime import datetime, timedelta

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7737151643))
BOT_TOKEN = "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A"
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_ID = int(os.environ.get("API_ID", 38876766))
API_HASH = os.environ.get("API_HASH", "e8d2d82f38704f4fcf171d3d35d3f811")

bot = telebot.TeleBot(BOT_TOKEN)
running_userbots = {}

# --- Flask Server (Render Port Binding Fix) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "AFK SYSTEM IS LIVE", 200

def run_flask():
    # Render က ပေးတဲ့ PORT ကို အတိအကျ သုံးရပါမယ်
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Database Handler ---
def safe_db_call(func, *args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        db = create_client(SUPABASE_URL, SUPABASE_KEY)
        return func(db, *args, **kwargs)
    finally:
        loop.close()

def get_user_data(db, uid):
    res = db.table("approved_users").select("*").eq("user_id", uid).execute()
    return res.data

def upsert_user(db, data):
    db.table("approved_users").upsert(data).execute()

def update_user(db, data, uid):
    db.table("approved_users").update(data).eq("user_id", uid).execute()

def get_all_active_users(db):
    res = db.table("approved_users").select("*").execute()
    return res.data

# --- Userbot Worker ---
def userbot_worker(uid, session_str, afk_msg):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def start_ub():
        try:
            ub = Client(name=f"ub_{uid}", session_string=session_str, 
                        api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await ub.start()
            running_userbots[uid] = ub
            @ub.on_message(filters.private & ~filters.me & ~filters.bot)
            async def handler(client, message):
                try:
                    me = await client.get_me()
                    if me.status in ["offline", "long_ago", "last_month"]:
                        await message.reply(afk_msg)
                except: pass
            await asyncio.Event().wait()
        except Exception as e:
            logging.error(f"Userbot {uid} failed: {e}")
    loop.run_until_complete(start_ub())

# --- Bot Handlers ---
@bot.message_handler(commands=['add'])
def add_user(m):
    if m.chat.id != ADMIN_ID: return
    try:
        parts = m.text.split()
        tid, days = int(parts[1]), int(parts[2])
        expiry = (datetime.now() + timedelta(days=days)).date().isoformat()
        safe_db_call(upsert_user, {"user_id": tid, "expiry_date": expiry})
        bot.reply_to(m, f"✅ User {tid} Added ({days} Days)")
    except Exception as e: bot.reply_to(m, f"❌ Error: {e}")

@bot.message_handler(commands=['start'])
def welcome(m):
    uid = m.chat.id
    res = safe_db_call(get_user_data, uid)
    if res:
        bot.send_message(uid, f"✅ ဝန်ဆောင်မှုရှိသည် ({res[0]['expiry_date']})\n\nString ပို့ပါ။")
        bot.register_next_step_handler(m, get_string)
    else: bot.send_message(uid, "❌ ဝယ်ယူရန် Admin @Cambai138 ဆီ ဆက်သွယ်ပါ။")

def get_string(m):
    bot.send_message(m.chat.id, "✅ AFK စာသား ပို့ပေးပါ။")
    bot.register_next_step_handler(m, lambda msg: finalize(msg, m.text))

def finalize(m, session_str):
    uid, afk_msg = m.chat.id, m.text
    safe_db_call(update_user, {"string": session_str, "afk_text": afk_msg}, uid)
    Thread(target=userbot_worker, args=(uid, session_str, afk_msg), daemon=True).start()
    bot.send_message(uid, "🚀 AFK Bot စတင်ပါပြီ။")

if __name__ == "__main__":
    # Flask ကို thread နဲ့ အရင် run ထားပါမယ်
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Startup ပြန်နှိုးခြင်း
    try:
        users = safe_db_call(get_all_active_users)
        for u in users:
            if u.get('string') and u.get('afk_text'):
                Thread(target=userbot_worker, args=(u['user_id'], u['string'], u['afk_text']), daemon=True).start()
    except: pass

    logging.info("Bot is starting polling...")
    bot.infinity_polling()
