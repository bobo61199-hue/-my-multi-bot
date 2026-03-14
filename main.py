import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from supabase import create_client
from pyrogram import Client, filters
from telebot.async_telebot import AsyncTeleBot

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A"
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_ID = int(os.environ.get("API_ID", 38876766))
API_HASH = os.environ.get("API_HASH", "e8d2d82f38704f4fcf171d3d35d3f811")

bot = AsyncTeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "AFK SYSTEM: ACTIVE", 200

def run_flask():
    # Render အတွက် Port Binding ကို သီးသန့် thread နဲ့ run ပါမယ်
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AFK Worker Function ---
async def start_afk(uid, session, text):
    try:
        ub = Client(
            name=f"u_{uid}", 
            session_string=session, 
            api_id=API_ID, 
            api_hash=API_HASH, 
            in_memory=True
        )
        await ub.start()
        
        @ub.on_message(filters.private & ~filters.me & ~filters.bot)
        async def afk_handler(c, m):
            try:
                me = await c.get_me()
                # Status က offline ဖြစ်နေမှ reply ပြန်ပါမယ်
                if me.status in ["offline", "long_ago"]:
                    await m.reply(text)
            except: pass
        
        logging.info(f"✅ Userbot {uid} is running.")
        await asyncio.Event().wait()
    except Exception as e:
        logging.error(f"❌ Userbot {uid} failed: {e}")

# --- Bot Commands ---
@bot.message_handler(commands=['start'])
async def welcome(m):
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    res = db.table("approved_users").select("*").eq("user_id", m.chat.id).execute()
    if res.data:
        await bot.reply_to(m, "✅ ဝန်ဆောင်မှုရှိပါသည်။ String Session ပို့ပေးပါ။")
    else:
        await bot.reply_to(m, "❌ ဝယ်ယူရန် Admin @Cambai138 ကို ဆက်သွယ်ပါ။")

# --- Main Engine ---
async def main():
    # ၁။ Port Binding အတွက် Flask ကို background မှာ နိုးမယ်
    Thread(target=run_flask, daemon=True).start()
    
    # ၂။ Database က User တွေကို တစ်ခါတည်း ပြန်နှိုးမယ်
    try:
        db = create_client(SUPABASE_URL, SUPABASE_KEY)
        users = db.table("approved_users").select("*").execute().data
        for u in users:
            if u.get('string') and u.get('afk_text'):
                asyncio.create_task(start_afk(u['user_id'], u['string'], u['afk_text']))
    except Exception as e:
        logging.error(f"Startup Database Error: {e}")

    # ၃။ Main Bot Polling ကို စတင်မယ်
    logging.info("🚀 Main Bot is starting...")
    await bot.polling(non_stop=True)

if __name__ == "__main__":
    # Python 3.14 ရဲ့ loop error ကို ကျော်ဖို့ manual loop ဆောက်တာပါ
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
