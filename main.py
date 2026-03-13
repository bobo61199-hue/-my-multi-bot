import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from supabase import create_client
from pyrogram import Client, filters
from telebot.async_telebot import AsyncTeleBot
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

# Async Bot & Global Storage
bot = AsyncTeleBot(BOT_TOKEN)
running_userbots = {}
app = Flask(__name__)

@app.route('/')
def health_check(): return "SYSTEM LIVE", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Database Setup (Inside Async) ---
async def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Userbot Worker ---
async def start_userbot(uid, session_str, afk_msg):
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
        
        logging.info(f"✅ Userbot {uid} started.")
        await asyncio.Event().wait()
    except Exception as e:
        logging.error(f"❌ Userbot {uid} failed: {e}")

# --- Main Bot Handlers ---
@bot.message_handler(commands=['start'])
async def send_welcome(m):
    db = await get_db()
    res = db.table("approved_users").select("*").eq("user_id", m.chat.id).execute()
    if res.data:
        await bot.reply_to(m, f"✅ ဝန်ဆောင်မှုရှိသည် ({res.data[0]['expiry_date']})\n\nString ပို့ပါ။")
    else:
        await bot.reply_to(m, "❌ ဝယ်ယူရန် Admin @Cambai138 ဆီ ဆက်သွယ်ပါ။")

# --- Startup & Main Loop ---
async def main():
    # Flask ကို Background မှာ run မယ်
    Thread(target=run_flask, daemon=True).start()
    
    # အရင်ရှိပြီးသား User တွေကို ပြန်နှိုးမယ်
    try:
        db = await get_db()
        users = db.table("approved_users").select("*").execute().data
        for u in users:
            if u.get('string') and u.get('afk_text'):
                asyncio.create_task(start_userbot(u['user_id'], u['string'], u['afk_text']))
    except Exception as e:
        logging.error(f"Startup Error: {e}")

    logging.info("🚀 Bot is Polling...")
    await bot.polling(non_stop=True)

if __name__ == "__main__":
    asyncio.run(main())

