import telebot
import os
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

bot = telebot.TeleBot(BOT_TOKEN)
running_userbots = {}
app = Flask('')

@app.route('/')
def home(): return "AFK SYSTEM: ONLINE"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- Helper Function: Database Call (Loop Error ကင်းစေရန်) ---
def db_query(action, table, data=None, filters=None):
    # ဒီနေရာမှာ loop အသစ်ဆောက်ပြီးမှ db ကို ခေါ်ပါမယ်
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    if action == "select":
        res = db.table(table).select("*").eq(filters[0], filters[1]).execute()
        return res.data
    elif action == "upsert":
        db.table(table).upsert(data).execute()
    elif action == "update":
        db.table(table).update(data).eq(filters[0], filters[1]).execute()
    elif action == "get_all":
        res = db.table(table).select("*").execute()
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
        except: pass

    loop.run_until_complete(start_ub())

# --- Bot Handlers ---
@bot.message_handler(commands=['add'])
def add_user(m):
    if m.chat.id != ADMIN_ID: return
    try:
        _, tid, days = m.text.split()
        expiry = (datetime.now() + timedelta(days=int(days))).date().isoformat()
        db_query("upsert", "approved_users", {"user_id": int(tid), "expiry_date": expiry})
        bot.reply_to(m, f"✅ User {tid} ကို {days} ရက် တိုးပေးပြီး။")
    except: bot.reply_to(m, "Format: /add [id] [days]")

@bot.message_handler(commands=['start'])
def welcome(m):
    uid = m.chat.id
    res = db_query("select", "approved_users", filters=("user_id", uid))
    if res:
        bot.send_message(uid, f"✅ ဝန်ဆောင်မှုရှိသည် ({res[0]['expiry_date']})\n\nString ပို့ပါ။")
        bot.register_next_step_handler(m, get_string)
    else: bot.send_message(uid, "❌ ဝယ်ယူရန် Admin @Cambai138 ဆီ ဆက်သွယ်ပါ။")

def get_string(m):
    bot.send_message(m.chat.id, "✅ AFK စာသား ပို့ပေးပါ။")
    bot.register_next_step_handler(m, lambda msg: finalize(msg, m.text))

def finalize(m, session_str):
    uid, afk_msg = m.chat.id, m.text
    db_query("update", "approved_users", {"string": session_str, "afk_text": afk_msg}, ("user_id", uid))
    Thread(target=userbot_worker, args=(uid, session_str, afk_msg), daemon=True).start()
    bot.send_message(uid, "🚀 AFK Bot စတင်ပါပြီ။")

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    
    # Startup 
    try:
        users = db_query("get_all", "approved_users")
        for u in users:
            if u.get('string') and u.get('afk_text'):
                Thread(target=userbot_worker, args=(u['user_id'], u['string'], u['afk_text']), daemon=True).start()
    except: pass

    print("Bot is Polling...")
    bot.infinity_polling()

