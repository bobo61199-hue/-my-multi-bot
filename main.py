import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from supabase_py_async import create_client  # Async Client ကို ပြောင်းသုံးထားပါတယ်
from pyrogram import Client, filters
from telebot.async_telebot import AsyncTeleBot

# --- Setup ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A"
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_ID = int(os.environ.get("API_ID", 38876766))
API_HASH = os.environ.get("API_HASH", "e8d2d82f38704f4fcf171d3d35d3f811")

bot = AsyncTeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home(): return "AFK SYSTEM LIVE", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AFK Logic ---
async def start_userbot(uid, session, text):
    try:
        ub = Client(name=f"u_{uid}", session_string=session, 
                    api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await ub.start()
        
        @ub.on_message(filters.private & ~filters.me & ~filters.bot)
        async def reply_handler(c, m):
            me = await c.get_me()
            if me.status in ["offline", "long_ago"]:
                await m.reply(text)
        
        await asyncio.Event().wait()
    except: pass

# --- Bot Commands ---
@bot.message_handler(commands=['start'])
async def welcome(m):
    # Async DB call
    db = await create_client(SUPABASE_URL, SUPABASE_KEY)
    res = await db.table("approved_users").select("*").eq("user_id", m.chat.id).execute()
    if res.data:
        await bot.reply_to(m, "✅ ဝန်ဆောင်မှုရှိပါသည်။ String Session ပို့ပေးပါ။")
    else:
        await bot.reply_to(m, "❌ ဝယ်ယူရန် @Cambai138 ကို ဆက်သွယ်ပါ။")

# --- Main Engine ---
async def main():
    # Flask ကို background မှာ မောင်းမယ် (Port binding error မတက်အောင်)
    Thread(target=run_flask, daemon=True).start()
    
    # Database ထဲက user တွေကို ပြန်နှိုးမယ်
    try:
        db = await create_client(SUPABASE_URL, SUPABASE_KEY)
        users = await db.table("approved_users").select("*").execute()
        for u in users.data:
            if u.get('string') and u.get('afk_text'):
                asyncio.create_task(start_userbot(u['user_id'], u['string'], u['afk_text']))
    except Exception as e:
        logging.error(f"DB Error: {e}")

    logging.info("🚀 Bot is Polling...")
    await bot.polling(non_stop=True)

if __name__ == "__main__":
    # Python 3.14 ရဲ့ asyncio loop ပြဿနာကို ဖြေရှင်းနည်း
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
