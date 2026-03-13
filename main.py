import asyncio
import os
import requests
import time
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, types
from supabase import create_client

# --- Flask Server ---
app = Flask('')

@app.route('/')
def home(): 
    return "AFK MULTI-BOT: SYSTEM ONLINE"

def run_flask():
    # Render က ပေးတဲ့ PORT ကို သုံးမယ်၊ မရှိရင် 10000
    port = int(os.environ.get("PORT", 10000))
    print(f"Flask Server starting on port {port}")
    app.run(host='0.0.0.0', port=port)

# --- Configuration ---
# Admin ID နဲ့ Database Key တွေကို Environment Variables ကနေပဲ ယူမယ်
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7737151643))
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xslvzwfizcvdbjckpsem.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzbHZ6d2ZpemN2ZGJqY2twc2VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzODc3ODYsImV4cCI6MjA4ODk2Mzc4Nn0.DC-XWrqBGno4vnWFPP2cPqBMG0zB-LEeKP7Hv6VPnc4")
API_ID = int(os.environ.get("API_ID", 38876766))
API_HASH = os.environ.get("API_HASH", "e8d2d82f38704f4fcf171d3d35d3f811")

# Database Connection
db = create_client(SUPABASE_URL, SUPABASE_KEY)
running_userbots = {}

# --- Userbot Starter ---
async def start_userbot(uid, session_str, afk_content):
    if uid in running_userbots:
        try: await running_userbots[uid].stop()
        except: pass

    async def run_ub():
        try:
            ub = Client(f"user_{uid}", session_string=session_str, api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await ub.start()
            running_userbots[uid] = ub
            
            @ub.on_message(filters.private & ~filters.me & ~filters.bot)
            async def afk_handler(client, message):
                try:
                    me = await client.get_me()
                    if me.status in ["offline", "long_ago", "last_month"]:
                        res = db.table("approved_users").select("afk_text").eq("user_id", uid).execute()
                        reply = res.data[0]['afk_text'] if res.data else afk_content
                        await message.reply(reply)
                except: pass
            
            await asyncio.Event().wait()
        except: await asyncio.sleep(60)

    asyncio.create_task(run_ub())

# --- Main Bot Logic ---
async def start_main_bot():
    bot = Client("main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    @bot.on_message(filters.command("start") & filters.private)
    async def welcome(c, m):
        uid = m.from_user.id
        res = db.table("approved_users").select("*").eq("user_id", uid).execute()
        if res.data:
            db.table("user_states").upsert({"user_id": uid, "state": "waiting"}).execute()
            await m.reply("✅ ဝန်ဆောင်မှုရှိသည်။ String Session ပို့ပေးပါ။")
        else:
            await m.reply("❌ ဝန်ဆောင်မှု မရှိပါ။")

    # အတည်ပြုပြီးသား User တွေ ပြန်နှိုးခြင်း
    await bot.start()
    try:
        users = db.table("approved_users").select("*").execute().data
        for u in users:
            if u.get('string'): await start_userbot(u['user_id'], u['string'], u['afk_text'])
    except: pass
    
    await asyncio.Event().wait()

# --- Entry Point ---
if __name__ == "__main__":
    # 1. Flask Thread နှိုးမယ်
    t = Thread(target=run_flask, daemon=True)
    t.start()
    
    # 2. Main Bot အတွက် Loop သီးသန့် ဆောက်မယ်
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_main_bot())
    except KeyboardInterrupt: pass
