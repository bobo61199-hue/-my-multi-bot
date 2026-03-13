import asyncio
import os
import requests
import time
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, types
from supabase import create_client

# --- Flask Server (Fix Port 10000) ---
app = Flask('')

@app.route('/')
def home(): 
    return "AFK MULTI-BOT: SYSTEM ONLINE"

def run_flask():
    port = 10000
    print(f"Flask Server starting on port {port}")
    app.run(host='0.0.0.0', port=port)

# --- Configuration ---
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7737151643))
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xslvzwfizcvdbjckpsem.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...") 
API_ID = int(os.environ.get("API_ID", 38876766))
API_HASH = os.environ.get("API_HASH", "e8d2d82f38704f4fcf171d3d35d3f811")

db = create_client(SUPABASE_URL, SUPABASE_KEY)
running_userbots = {}

async def start_userbot(uid, session_str, afk_content):
    if uid in running_userbots:
        try: await running_userbots[uid].stop()
        except: pass

    ub = Client(
        name=f"afk_{uid}", 
        session_string=session_str, 
        api_id=API_ID, 
        api_hash=API_HASH, 
        in_memory=True
    )
    
    @ub.on_message(filters.private & ~filters.me & ~filters.bot)
    async def afk_handler(client, message):
        try:
            me = await client.get_me()
            if me.status in ["offline", "long_ago", "last_month"]:
                res = db.table("approved_users").select("afk_text").eq("user_id", uid).execute()
                reply = res.data[0]['afk_text'] if res.data else afk_content
                if reply.startswith("photo:"): await message.reply_photo(reply.replace("photo:", ""))
                elif reply.startswith("sticker:"): await message.reply_sticker(reply.replace("sticker:", ""))
                else: await message.reply(reply)
        except: pass

    await ub.start()
    running_userbots[uid] = ub

async def main_bot():
    bot = Client("main_api_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    @bot.on_message(filters.command("start") & filters.private)
    async def start_handler(c, m):
        uid = m.from_user.id
        res = db.table("approved_users").select("*").eq("user_id", uid).execute()
        if res.data:
            db.table("user_states").upsert({"user_id": uid, "state": "awaiting_string"}).execute()
            await m.reply(f"✅ ဝန်ဆောင်မှုရှိပါသည်။ (Expiry: {res.data[0]['expiry_date']})\n\nString Session ပို့ပေးပါ။")
        else:
            await m.reply("❌ ဝန်ဆောင်မှု မဝယ်ရသေးပါ။ @Cambai138 ကို ဆက်သွယ်ပါ။")

    # ... (တခြား command တွေက အတူတူပဲမို့ နေရာသက်သာအောင် ချန်ခဲ့မယ်၊ ဒါပေမဲ့ မင်း code အဟောင်းထဲက command တွေ အကုန်ပြန်ထည့်ပါ)

    await bot.start()
    
    # ရှိပြီးသား userbots တွေနှိုးမယ်
    try:
        existing = db.table("approved_users").select("*").execute().data
        for u in existing:
            if u.get('string'): await start_userbot(u['user_id'], u['string'], u['afk_text'])
    except: pass

    print("--- BOT IS FULLY ONLINE ---")
    await asyncio.Event().wait()

# --- Entry Point (The Fix) ---
if __name__ == "__main__":
    # Flask ကို thread နဲ့အရင်မောင်းမယ်
    Thread(target=run_flask, daemon=True).start()
    
    # Event loop ကို manually ဆောက်ပြီး run တဲ့နည်း
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_bot())
    except KeyboardInterrupt:
        pass
