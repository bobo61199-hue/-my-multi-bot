import telebot
import os
import time
from threading import Thread
from flask import Flask
from supabase import create_client
from pyrogram import Client, filters
from datetime import datetime, timedelta

# --- Setup ---
app = Flask('')
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ADMIN_ID = 7737151643 # မင်းရဲ့ ID

bot = telebot.TeleBot(BOT_TOKEN)
db = create_client(SUPABASE_URL, SUPABASE_KEY)
running_userbots = {}

# --- Flask Server ---
@app.route('/')
def home(): return "AFK SYSTEM IS LIVE"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- Userbot Runner ---
def start_userbot(uid, session_str, afk_text):
    # Pyrogram ကို နောက်ကွယ်မှာ loop နဲ့ run တာ
    async def run():
        try:
            ub = Client(f"user_{uid}", session_string=session_str, api_id=38876766, api_hash="e8d2d82f38704f4fcf171d3d35d3f811")
            await ub.start()
            running_userbots[uid] = ub
            
            @ub.on_message(filters.private & ~filters.me)
            async def reply(client, message):
                me = await client.get_me()
                if me.status in ["offline", "long_ago"]:
                    await message.reply(afk_text)
            
            print(f"✅ Userbot {uid} started!")
        except: pass

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())
    loop.run_forever()

# --- Main Bot (Telebot) Handlers ---

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.chat.id
    # Database မှာ ဝယ်ထားတဲ့ user လား စစ်မယ်
    res = db.table("approved_users").select("*").eq("user_id", uid).execute()
    if res.data:
        bot.send_message(uid, f"✅ ဝန်ဆောင်မှုရှိပါသည်။ (သက်တမ်း: {res.data[0]['expiry_date']})\n\nString Session ပို့ပေးပါ။")
        bot.register_next_step_handler(m, get_string)
    else:
        bot.send_message(uid, "❌ ဝန်ဆောင်မှု မဝယ်ရသေးပါ။ ဝယ်ယူရန် Admin ကို ဆက်သွယ်ပါ။")

def get_string(m):
    uid = m.chat.id
    string = m.text
    bot.send_message(uid, "✅ String ရပါပြီ။ Offline ဖြစ်ချိန် ပြန်စေချင်တဲ့ စာသား ပို့ပေးပါ။")
    bot.register_next_step_handler(m, lambda msg: save_and_start(msg, string))

def save_and_start(m, string):
    uid = m.chat.id
    afk_text = m.text
    # Database မှာ update လုပ်မယ်
    db.table("approved_users").update({"string": string, "afk_text": afk_text}).eq("user_id", uid).execute()
    
    # Userbot ကို thread အသစ်နဲ့ နှိုးမယ်
    Thread(target=start_userbot, args=(uid, string, afk_text), daemon=True).start()
    bot.send_message(uid, "🚀 AFK Bot စတင်အလုပ်လုပ်ပါပြီ။ လိုင်းဆင်းသွားရင် auto reply ပြန်ပေးပါလိမ့်မယ်။")

# --- Admin Section ---
@bot.message_handler(commands=['add'])
def add_user(m):
    if m.chat.id != ADMIN_ID: return
    try:
        args = m.text.split()
        target_id = args[1]
        days = int(args[2]) # ၁ လ ဆို ၃၀၊ တသက်သာဆို ၉၉၉၉
        expiry = (datetime.now() + timedelta(days=days)).date().isoformat()
        
        db.table("approved_users").upsert({"user_id": target_id, "expiry_date": expiry}).execute()
        bot.send_message(ADMIN_ID, f"✅ User {target_id} ကို {days} ရက် သတ်မှတ်ပေးလိုက်ပါပြီ။")
    except:
        bot.send_message(ADMIN_ID, "⚠️ Format: /add [user_id] [days]")

# --- Execution ---
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    print("Bot is polling...")
    bot.infinity_polling()
