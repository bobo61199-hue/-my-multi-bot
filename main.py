import asyncio
import os
import requests
import time
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, types
from supabase import create_client

# --- Flask Server (Render အတွက် Port 10000 Fix လုပ်ထားသည်) ---
app = Flask('')

@app.route('/')
def home(): 
    return "AFK MULTI-BOT: SYSTEM ONLINE"

def run_flask():
    # မင်းသုံးချင်တဲ့ Port 10000 ကို ဒီမှာ အသေထည့်ထားပေးတယ်
    port = 10000
    print(f"Flask Server is starting on Port: {port}")
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # သင့် Render App URL (URL အသစ်နဲ့ အမြဲစစ်ပေးပါ)
    URL = "https://my-multi-bot-7nrt.onrender.com"
    while True:
        try: 
            requests.get(URL, timeout=15)
        except: 
            pass
        time.sleep(300)

# --- Configuration (Environment Variables) ---
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7737151643))
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xslvzwfizcvdbjckpsem.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzbHZ6d2ZpemN2ZGJqY2twc2VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzODc3ODYsImV4cCI6MjA4ODk2Mzc4Nn0.DC-XWrqBGno4vnWFPP2cPqBMG0zB-LEeKP7Hv6VPnc4")
API_ID = int(os.environ.get("API_ID", 38876766))
API_HASH = os.environ.get("API_HASH", "e8d2d82f38704f4fcf171d3d35d3f811")

db = create_client(SUPABASE_URL, SUPABASE_KEY)
running_userbots = {}

# --- Userbot Logic ---
async def start_userbot(uid, session_str, afk_content):
    if uid in running_userbots:
        try: 
            await running_userbots[uid].stop()
        except: 
            pass

    async def run():
        while True:
            try:
                ub = Client(
                    name=f"afk_{uid}", 
                    session_string=session_str, 
                    api_id=API_ID, 
                    api_hash=API_HASH, 
                    in_memory=True
                )
                await ub.start()
                running_userbots[uid] = ub
                
                @ub.on_message(filters.private & ~filters.me & ~filters.bot)
                async def afk_handler(client, message):
                    try:
                        me = await client.get_me()
                        if me.status in ["offline", "long_ago", "last_month"]:
                            res = db.table("approved_users").select("afk_text").eq("user_id", uid).execute()
                            reply = res.data[0]['afk_text'] if res.data else afk_content
                            
                            if reply.startswith("photo:"):
                                await message.reply_photo(reply.replace("photo:", ""))
                            elif reply.startswith("sticker:"):
                                await message.reply_sticker(reply.replace("sticker:", ""))
                            else:
                                await message.reply(reply)
                    except: 
                        pass
                
                await asyncio.Event().wait()
            except: 
                await asyncio.sleep(60)
                
    asyncio.create_task(run())

# --- Main Bot ---
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

    @bot.on_message(filters.command("stats") & filters.user(ADMIN_ID))
    async def stats_handler(c, m):
        total = db.table("approved_users").select("*", count="exact").execute().count
        active = len(running_userbots)
        await m.reply(f"📊 **System Stats**\n\n👥 Total Users: {total}\n⚡ Active Userbots: {active}")

    @bot.on_message(filters.command("add") & filters.user(ADMIN_ID))
    async def add_user(c, m):
        try:
            tid = int(m.text.split()[1])
            kb = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("၁ လ", callback_data=f"dur_{tid}_30")]])
            await m.reply(f"👤 User: `{tid}` သက်တမ်းရွေးပါ။", reply_markup=kb)
        except: 
            pass

    @bot.on_callback_query(filters.regex(r"^dur_"))
    async def set_dur(c, q):
        uid, days = int(q.data.split("_")[1]), int(q.data.split("_")[2])
        expiry = (datetime.now() + timedelta(days=days)).date().isoformat()
        db.table("approved_users").upsert({"user_id": uid, "expiry_date": expiry}).execute()
        await q.edit_message_text(f"✅ User `{uid}` ထည့်ပြီး။")

    @bot.on_message(filters.private & filters.text & ~filters.command(["start", "add", "stats"]))
    async def input_handler(c, m):
        uid = m.from_user.id
        s_res = db.table("user_states").select("state").eq("user_id", uid).execute()
        if not s_res.data: return
        state = s_res.data[0]['state']

        if state == "awaiting_string":
            db.table("pending_users").upsert({"user_id": uid, "string": m.text}).execute()
            db.table("user_states").update({"state": "awaiting_afk"}).eq("user_id", uid).execute()
            await m.reply("✅ String ရပြီ။ AFK စာသား ပို့ပေးပါ။")
        
        elif state == "awaiting_afk":
            db.table("pending_users").update({"afk_text": m.text}).eq("user_id", uid).execute()
            db.table("user_states").update({"state": "submitted"}).eq("user_id", uid).execute()
            kb = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("✅ Accept", callback_data=f"app_{uid}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{uid}")]])
            await bot.send_message(ADMIN_ID, f"🔔 Request: `{uid}`\nText: {m.text}", reply_markup=kb)
            await m.reply("⏳ Admin ဆီ ခွင့်ပြုချက် တောင်းခံထားပါသည်။")

    @bot.on_callback_query(filters.regex(r"^(app_|rej_)"))
    async def admin_dec(c, q):
        action, uid = q.data.split("_")[0], int(q.data.split("_")[1])
        if action == "app":
            p_res = db.table("pending_users").select("*").eq("user_id", uid).execute()
            if p_res.data:
                data = p_res.data[0]
                db.table("approved_users").update({"string": data['string'], "afk_text": data['afk_text']}).eq("user_id", uid).execute()
                await start_userbot(uid, data['string'], data['afk_text'])
                await bot.send_message(uid, "🎉 Admin က အတည်ပြုလိုက်ပါပြီ။ Bot စတင်အလုပ်လုပ်ပါပြီ။")
                await q.edit_message_text(f"✅ Approved: {uid}")
        else:
            await bot.send_message(uid, "❌ Admin က ငြင်းပယ်လိုက်ပါသည်။")
            await q.edit_message_text(f"❌ Rejected: {uid}")

    await bot.start()
    
    # ပြန်တက်လာရင် ရှိပြီးသား Userbot တွေ ပြန်နှိုးခြင်း
    try:
        existing = db.table("approved_users").select("*").execute().data
        if existing:
            for u in existing:
                if u.get('string'): 
                    await start_userbot(u['user_id'], u['string'], u['afk_text'])
    except: 
        pass
            
    await asyncio.Event().wait()

# --- Execution ---
if __name__ == "__main__":
    # Flask နဲ့ Keep Alive ကို Thread တွေနဲ့ သီးသန့်ခွဲမောင်းမယ်
    t1 = Thread(target=run_flask, daemon=True)
    t1.start()
    
    t2 = Thread(target=keep_alive, daemon=True)
    t2.start()
    
    # Main Bot ကို Asyncio Event Loop နဲ့ run မယ်
    async def run_app():
        try:
            await main_bot()
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")

    try:
        asyncio.run(run_app())
    except (KeyboardInterrupt, SystemExit):
        pass

