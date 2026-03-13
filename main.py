import telebot
import os
import time
import asyncio
from threading import Thread
from flask import Flask
from supabase import create_client
from pyrogram import Client, filters
from datetime import datetime, timedelta

# --- Configuration ---
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7737151643))
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_ID = int(os.environ.get("API_ID", 38876766))
API_HASH = os.environ.get("API_HASH", "e8d2d82f38704f4fcf171d3d35d3f811")

bot = telebot.TeleBot(BOT_TOKEN)
db = create_client(SUPABASE_URL, SUPABASE_KEY)
running_userbots = {}
app = Flask('')

@app.route('/')
def home(): return "AFK SYSTEM: ONLINE"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- Userbot Logic ---
async def run_afk_userbot(uid, session_str, afk_msg):
    try:
        ub = Client(f"ub_{uid}", session_string=session_str, api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await ub.start()
        running_userbots[uid] = ub
        
        @ub.on_message(filters.private & ~filters.me & ~filters.bot)
        async def handler(client, message):
            try:
                me = await client.get_me()
                # Status စစ်ခြင်း (Offline ဖြစ်မှ ပြန်မည်)
                if me.status in ["offline", "long_ago", "last_month"]:
                    await message.reply(afk_msg)
            except: pass
        
        await asyncio.Event().wait()
    except Exception as e:
        print(f"❌ Userbot {uid} Error: {e}")

def start_ub_thread(uid, session_str, afk_msg):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_afk_userbot(uid, session_str, afk_msg))

# --- Bot Handlers ---
@bot.message_handler(commands=['add'])
def add_user(m):
    if m.chat.id != ADMIN_ID: return
    try:
        parts = m.text.split()
        target_id = int(parts[1])
        days = int(parts[2])
        expiry = (datetime.now() + timedelta(days=days)).date().isoformat()
        db.table("approved_users").upsert({"user_id": target_id, "expiry_date": expiry}).execute()
        bot.reply_to(m, f"✅ User {target_id} - {days} ရက် တိုးပေးပြီး။")
    except:
        bot.reply_to(m, "⚠️ Format: /add [user_id] [days]")

@bot.message_handler(commands=['start'])
def welcome(m):
    uid = m.chat.id
    res = db.table("approved_users").select("*").eq("user_id", uid).execute()
    if res.data:
        expiry = res.data[0]['expiry_date']
        bot.send_message(uid, f"✅ ဝန်ဆောင်မှုရှိသည် ({expiry})\n\nString Session ကို ပို့ပေးပါ။")
        bot.register_next_step_handler(m, get_string)
    else:
        bot.send_message(uid, "❌ ဝန်ဆောင်မှု မရှိပါ။ Admin @Cambai138 ဆီ ဝယ်ယူပါ။")

def get_string(m):
    uid, session_str = m.chat.id, m.text
    if len(session_str) < 50: # အကြမ်းဖျင်း String Session ဟုတ်မဟုတ်စစ်ခြင်း
        bot.send_message(uid, "❌ String Session မှားယွင်းနေပုံရသည်။ ပြန်ပို့ပါ။")
        return
    bot.send_message(uid, "✅ AFK စာသား ပို့ပေးပါ။")
    bot.register_next_step_handler(m, lambda msg: finalize(msg, session_str))

def finalize(m, session_str):
    uid, afk_msg = m.chat.id, m.text
    db.table("approved_users").update({"string": session_str, "afk_text": afk_msg}).eq("user_id", uid).execute()
    Thread(target=start_ub_thread, args=(uid, session_str, afk_msg), daemon=True).start()
    bot.send_message(uid, "🚀 AFK Bot စတင်အလုပ်လုပ်ပါပြီ။")

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    # Startup ပြန်နှိုးခြင်း
    try:
        users = db.table("approved_users").select("*").execute().data
        for u in users:
            if u.get('string') and u.get('afk_text'):
                # တစ်ခုချင်းစီကို Error handling လုပ်ပြီး နှိုးခြင်း
                Thread(target=start_ub_thread, args=(u['user_id'], u['string'], u['afk_text']), daemon=True).start()
    except Exception as e:
        print(f"Startup Error: {e}")

    print("Main Bot is starting...")
    bot.infinity_polling(timeout=60)
