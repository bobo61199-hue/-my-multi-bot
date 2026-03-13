import asyncio
import os
import requests
import time
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, types
from supabase import create_client

# --- Flask & No-Sleep ---
app = Flask('')
@app.route('/')
def home(): return "AFK PRO SHOP: ACTIVE"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    URL = "https://your-bot-name.onrender.com" 
    while True:
        try: requests.get(URL, timeout=15)
        except: pass
        time.sleep(300)

# --- Configuration ---
ADMIN_ID = 7737151643 
BOT_TOKEN = "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A"
SUPABASE_URL = "https://xslvzwfizcvdbjckpsem.supabase.co"
SUPABASE_KEY = ''''eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzbHZ6d2ZpemN2ZGJqY2twc2VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzODc3ODYsImV4cCI6MjA4ODk2Mzc4Nn0.DC-XWrqBGno4vnWFPP2cPqBMG0zB-LEeKP7Hv6VPnc4""

API_ID = 38876766
API_HASH = "e8d2d82f38704f4fcf171d3d35d3f811"

db = create_client(SUPABASE_URL, SUPABASE_KEY)
running_userbots = {}

# --- Userbot Runner Logic ---
async def start_userbot(uid, session_str, afk_text):
    if uid in running_userbots:
        try: await running_userbots[uid].stop()
        except: pass

    async def run():
        while True:
            try:
                async with Client(f"afk_{uid}", session_string=session_str, api_id=API_ID, api_hash=API_HASH) as ub:
                    running_userbots[uid] = ub
                    @ub.on_message(filters.private & ~filters.me)
                    async def afk_handler(client, message):
                        try:
                            me = await client.get_me()
                            if me.status in ["offline", "long_ago", "last_month"]:
                                current_data = db.table("approved_users").select("afk_text").eq("user_id", uid).execute()
                                reply_msg = current_data.data[0]['afk_text'] if current_data.data else afk_text
                                await message.reply(reply_msg)
                        except: pass
                    await asyncio.Event().wait()
            except Exception as e:
                if "AUTH_KEY_INVALID" in str(e):
                    try: await Client("notify", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN).send_message(ADMIN_ID, f"⚠️ User `{uid}` String Invalid!")
                    except: pass
                    break
                await asyncio.sleep(30)
    asyncio.create_task(run())

# --- Expiry Checker Loop ---
async def expiry_checker(bot):
    while True:
        try:
            users = db.table("approved_users").select("*").execute().data
            today = datetime.now().date()
            for u in users:
                if u['expiry_date']:
                    exp = datetime.fromisoformat(u['expiry_date']).date()
                    if today > exp:
                        uid = u['user_id']
                        db.table("approved_users").delete().eq("user_id", uid).execute()
                        if uid in running_userbots:
                            await running_userbots[uid].stop()
                            del running_userbots[uid]
                        try: await bot.send_message(uid, "⚠️ သင့်ဝန်ဆောင်မှု သက်တမ်းကုန်သွားပါပြီ။ ထပ်မံဝယ်ယူရန် @Cambai138 ကို ဆက်သွယ်ပါ။")
                        except: pass
        except: pass
        await asyncio.sleep(3600)

# --- Main API Bot ---
async def main_bot():
    bot = Client("main_api_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    @bot.on_message(filters.command("start") & filters.private)
    async def start_handler(c, m):
        uid = m.from_user.id
        res = db.table("approved_users").select("*").eq("user_id", uid).execute()
        if res.data:
            db.table("user_states").upsert({"user_id": uid, "state": "awaiting_string"}).execute()
            await m.reply(f"✅ ဝန်ဆောင်မှုရှိပါသည်။ (သက်တမ်းကုန်ရက်: {res.data[0]['expiry_date']})\nအသုံးပြုရန် **String Session** ကို ပို့ပေးပါ။")
        else:
            keyboard = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("🛒 ဝယ်ယူရန် ဆက်သွယ်ပါ", url="https://t.me/Cambai138")]])
            await m.reply("❌ **ဝန်ဆောင်မှု မဝယ်ရသေးပါ**\n@Cambai138 ဆီတွင် အရင်ဝယ်ယူပေးပါ။", reply_markup=keyboard)

    # Admin Add with Buttons
    @bot.on_message(filters.command("add") & filters.user(ADMIN_ID))
    async def add_user_start(c, m):
        try:
            target_id = int(m.text.split()[1])
            keyboard = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("၁ လ (ရက် ၃၀)", callback_data=f"dur_{target_id}_30")],
                [types.InlineKeyboardButton("၂ လ (ရက် ၆၀)", callback_data=f"dur_{target_id}_60")],
                [types.InlineKeyboardButton("တစ်သက်တာ (Lifetime)", callback_data=f"dur_{target_id}_9999")]
            ])
            await m.reply(f"👤 User ID: `{target_id}` အတွက် သက်တမ်းရွေးချယ်ပါ-", reply_markup=keyboard)
        except: await m.reply("Usage: `/add [User_ID]`")

    @bot.on_callback_query(filters.regex(r"^dur_"))
    async def set_duration(c, q):
        data = q.data.split("_")
        uid, days = int(data[1]), int(data[2])
        expiry = (datetime.now() + timedelta(days=days)).date().isoformat()
        db.table("approved_users").upsert({"user_id": uid, "expiry_date": expiry, "name": "Buyer"}).execute()
        exp_txt = "Lifetime" if days > 5000 else expiry
        await q.edit_message_text(f"✅ User `{uid}` အား ထည့်ပြီးပါပြီ။\n📅 သက်တမ်းကုန်ရက်: `{exp_txt}`")
        try: await c.send_message(uid, f"🎉 Admin က အသုံးပြုခွင့်ပေးလိုက်ပါပြီ။\n📅 သက်တမ်းကုန်ရက်: `{exp_txt}`\n/start ကိုနှိပ်ပါ။")
        except: pass

    @bot.on_message(filters.command("status") & filters.private)
    async def status_handler(c, m):
        uid = m.from_user.id
        res = db.table("approved_users").select("*").eq("user_id", uid).execute()
        if not res.data: return await m.reply("❌ ဝယ်ယူထားခြင်း မရှိပါ။")
        is_run = "🟢 Active" if uid in running_userbots else "🔴 Inactive"
        await m.reply(f"📊 **Status:** {is_run}\n📅 **Expiry:** {res.data[0]['expiry_date']}")

    @bot.on_message(filters.private & filters.text & ~filters.command(["start", "add", "status"]))
    async def input_handler(c, m):
        uid = m.from_user.id
        state_res = db.table("user_states").select("state").eq("user_id", uid).execute()
        if not state_res.data: return
        state = state_res.data[0]['state']
        if state == "awaiting_string":
            db.table("pending_users").upsert({"user_id": uid, "string": m.text, "name": m.from_user.first_name}).execute()
            db.table("user_states").update({"state": "awaiting_afk"}).eq("user_id", uid).execute()
            await m.reply("✅ String ရပါပြီ။ Offline ဖြစ်ရင် ပြန်ချင်တဲ့ **စာသား** ပို့ပေးပါ။")
        elif state == "awaiting_afk":
            db.table("pending_users").update({"afk_text": m.text}).eq("user_id", uid).execute()
            db.table("user_states").update({"state": "submitted"}).eq("user_id", uid).execute()
            keyboard = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{uid}")]])
            await bot.send_message(ADMIN_ID, f"🔔 **Update Request**\nID: `{uid}`\nText: {m.text}", reply_markup=keyboard)
            await m.reply("⏳ Admin အတည်ပြုချက် စောင့်ဆိုင်းနေပါသည်။")

    @bot.on_callback_query(filters.regex(r"^app_"))
    async def approve_cb(c, q):
        uid = int(q.data.split("_")[1])
        data = db.table("pending_users").select("*").eq("user_id", uid).execute().data[0]
        db.table("approved_users").update({"string": data['string'], "afk_text": data['afk_text']}).eq("user_id", uid).execute()
        await start_userbot(uid, data['string'], data['afk_text'])
        await bot.send_message(uid, "🎉 Bot စတင်အလုပ်လုပ်ပါပြီ။")
        await q.edit_message_text(f"✅ Approved: {uid}")

    await bot.start()
    asyncio.create_task(expiry_checker(bot))
    await asyncio.Event().wait()

async def main():
    existing = db.table("approved_users").select("*").execute().data
    tasks = [main_bot()]
    for u in existing:
        if u.get('string'):
            await start_userbot(u['user_id'], u['string'], u['afk_text'])
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    Thread(target=keep_alive, daemon=True).start()
    asyncio.run(main())
