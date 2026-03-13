import asyncio
import os
import requests
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from supabase import create_client

# --- Flask Server (Render Port Binding အတွက်) ---
app = Flask('')

@app.route('/')
def home(): 
    return "AFK SYSTEM IS LIVE"

def run_flask():
    # Render Dashboard က PORT ကို ယူမယ်၊ မရှိရင် 10000 သုံးမယ်
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Configuration ---
# မင်းရဲ့ Environment Variables တွေ အကုန်ဒီမှာ ယူထားတယ်
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")

db = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Bot Logic ---
async def start_services():
    bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    
    @bot.on_message(filters.command("start") & filters.private)
    async def start(c, m):
        await m.reply("✅ Bot အလုပ်လုပ်နေပါပြီဟျောင့်။")

    print("Starting Telegram Bot...")
    await bot.start()
    
    # Userbot တွေ ပြန်နှိုးတဲ့အပိုင်း (Error မတက်အောင် try အုပ်ထားတယ်)
    try:
        users = db.table("approved_users").select("*").execute().data
        for u in users:
            if u.get('string'):
                # ဒီမှာ မင်းရဲ့ userbot logic ကို ထည့်ပါ
                pass
    except Exception as e:
        print(f"DB Error: {e}")

    # Loop ကို အမြဲပွင့်နေအောင် လုပ်ထားခြင်း
    await asyncio.Event().wait()

# --- Main Entry Point ---
if __name__ == "__main__":
    # Flask ကို Thread နဲ့ အရင်နှိုးမယ် (No open ports error မတက်အောင်)
    t = Thread(target=run_flask, daemon=True)
    t.start()
    
    # Event Loop ပြဿနာကို ဖြေရှင်းရန်
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        pass
