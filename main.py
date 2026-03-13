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
def home(): return "RUNNING", 200

def run_flask():
    # Render အတွက် Port Binding ကို သီးသန့် thread နဲ့ run တာ ပိုစိတ်ချရပါတယ်
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AFK Worker ---
async def start_afk(uid, session, text):
    try:
        ub = Client(name=f"u_{uid}", session_string=session, 
                    api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await ub.start()
        
        @ub.on_message(filters.private & ~filters.me & ~filters.bot)
        async def afk_handler(c, m):
            me = await c.get_me()
            if me.status in ["offline", "long_ago"]:
                await m.reply(text)
        
        await asyncio.Event().wait()
    except: pass

# --- Bot Command ---
@bot.message_handler(commands=['start'])
async def welcome(m):
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    res = db.table("approved_users").select("*").eq("user_id", m.chat.id).execute()
    if res.data:
        await bot.reply_to(m, "✅ ဝန်ဆောင်မှုရှိပါသည်။ String ပို့ပေးပါ။")
    else:
        await bot.reply_to(m, "❌ ဝယ်ယူရန် @Cambai138 ကို ဆက်သွယ်ပါ။")

# --- Main Engine ---
async def main():
    # ၁။ Flask ကို အရင်နိုးမယ်
    Thread(target=run_flask, daemon=True).start()
    
    # ၂။ Database က User တွေကို ပြန်နှိုးမယ်
    try:
        db = create_client(SUPABASE_URL, SUPABASE_KEY)
        users = db.table("approved_users").select("*").execute().data
        for u in users:
            if u.get('string') and u.get('afk_text'):
                asyncio.create_task(start_afk(u['user_id'], u['string'], u['afk_text']))
    except: pass

    # ၃။ Bot ကို Polling စလုပ်မယ်
    await bot.polling(non_stop=True)

if __name__ == "__main__":
    # Python 3.14 ရဲ့ loop error ကို ကျော်ဖို့ loop ကို သေချာသတ်မှတ်ပေးရပါတယ်
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
