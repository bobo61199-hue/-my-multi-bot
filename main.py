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
BOT_TOKEN = "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A"
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_ID = int(os.environ.get("API_ID", 38876766))
API_HASH = os.environ.get("API_HASH", "e8d2d82f38704f4fcf171d3d35d3f811")

# Bot & DB Initialization
bot = telebot.TeleBot(BOT_TOKEN)
db = create_client(SUPABASE_URL, SUPABASE_KEY)
running_userbots = {}
app = Flask('')

@app.route('/')
def home(): return "AFK SYSTEM: ONLINE"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- Userbot Worker (ဒီအပိုင်းက Error တက်နေတာကို ရှင်းပေးပါလိမ့်မယ်) ---
def userbot_worker(uid, session_str, afk_msg):
    # Thread တစ်ခုစီအတွက် loop အသစ်တစ်ခု အမြဲဆောက်ပေးရပါတယ်
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def start_ub():
        try:
            ub = Client(
                name=f"session_{uid}", 
                session_string=session_str, 
                api_id=API_ID, 
                api_hash=API_HASH, 
                in_memory=True
            )
            await ub.start()
            running_userbots[uid] = ub
            
            @ub.on_message(filters.private & ~filters.me & ~filters.bot)
            async def handler(client, message):
                try:
                    me = await client.get_me()
                    if me.status in ["offline", "long_ago", "last_month"]:
                        await message.reply(afk_msg)
                except: pass
            
            # Bot ကို အရှင်ထားရန်
            await asyncio.Event().wait()
        except Exception as e:
            print(f"❌ Userbot {uid} Failed: {e}")

    loop.run_until_complete(start_ub())

# --- Admin Handlers ---
@bot.message_handler(commands=['add'])
def add_user(m):
    if m.chat.id != ADMIN_ID: return
    try:
        _, tid, days = m.text.split()
        expiry = (datetime.now() + timedelta(days=int(days))).date().isoformat()
        db.table("approved_users").upsert({"user_id": int(tid), "expiry_date": expiry}).execute()
        bot.reply_to(m, f"✅ User {tid} - {days} ရက် တိုးပေးပြီး။")
    except: bot.reply_to(m, "⚠️ Use: /add [id] [days]")

# --- User Handlers ---
@bot.message_handler(commands=['start'])
def welcome(m):
    uid = m.chat.id
    res = db.table("approved_users").select("*").eq("user_id", uid).execute()
    if res.data:
        bot.send_message(uid, f"✅ ဝန်ဆောင်မှုရှိသည် ({res.data[0]['expiry_date']})\n\nString Session ကို ပို့ပေးပါ။")
        bot.register_next_step_handler(m, get_string)
    else: bot.send_message(uid, "❌ ဝယ်ယူရန် Admin @Cambai138 ဆီ ဆက်သွယ်ပါ။")

def get_string(m):
    bot.send_message(m.chat.id, "✅ AFK စာသား ပို့ပေးပါ။")
    bot.register_next_step_handler(m, lambda msg: finalize(msg, m.text))

def finalize(m, session_str):
    uid, afk_msg = m.chat.id, m.text
    db.table("approved_users").update({"string": session_str, "afk_text": afk_msg}).eq("user_id", uid).execute()
    Thread(target=userbot_worker, args=(uid, session_str, afk_msg), daemon=True).start()
    bot.send_message(uid, "🚀 AFK Bot စတင်ပါပြီ။")

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    
    # Startup: အရင်ရှိပြီးသားသူတွေကို ပြန်နှိုးခြင်း
    try:
        users = db.table("approved_users").select("*").execute().data
        for u in users:
            if u.get('string') and u.get('afk_text'):
                Thread(target=userbot_worker, args=(u['user_id'], u['string'], u['afk_text']), daemon=True).start()
    except: pass

    print("Main Bot Starting...")
    bot.infinity_polling()
