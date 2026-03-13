import asyncio
import os
import requests
import time
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, types
from supabase import create_client

# --- ၁။ Flask Server (Render အတွက် ၂၄ နာရီ နိုးကြားစေရန်) ---
app = Flask('')
@app.route('/')
def home(): 
    return "AFK PRO SHOP: ACTIVE 24/7"

def run_flask():
    # Render Dashboard မှာ PORT variable ကို 8080 ပေးရန်လိုအပ်သည်
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    # Render မှာ Deploy ပြီးလို့ ရလာမယ့် URL ကို ဒီနေရာမှာ အစားထိုးပါ
    URL = "https://your-bot-name.onrender.com" 
    while True:
        try: 
            requests.get(URL, timeout=15)
        except: 
            pass
        time.sleep(300) # ၅ မိနစ်တစ်ခါ သူ့ကိုယ်သူ ပြန်နှိုးမည်

# --- ၂။ Configuration & Database ---
ADMIN_ID = 7737151643 
BOT_TOKEN = "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A"
SUPABASE_URL = "https://xslvzwfizcvdbjckpsem.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzbHZ6d2ZpemN2ZGJqY2twc2VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzODc3ODYsImV4cCI6MjA4ODk2Mzc4Nn0.DC-XWrqBGno4vnWFPP2cPqBMG0zB-LEeKP7Hv6VPnc4"

API_ID = 38876766
API_HASH = "e8d2d82f38704f4fcf171d3d35d3f811"

db = create_client(SUPABASE_URL, SUPABASE_KEY)
running_userbots = {}

# --- ၃။ Userbot Runner (User တစ်ယောက်ချင်းစီအတွက် သီးသန့် Run ပေးမည့်အပိုင်း) ---
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
                            # User က Offline ဖြစ်နေမှသာ စာပြန်မည်
                            if me.status in ["offline", "long_ago", "last_month"]:
                                res = db.table("approved_users").select("afk_text").eq("user_id", uid).execute()
                                reply_msg = res.data[0]['afk_text'] if res.data else afk_text
                                await message.reply(reply_msg)
                        except: pass
                    await asyncio.Event().wait()
            except Exception as e:
                if "AUTH_KEY_INVALID" in str(e):
                    await Client("notify", API_ID, API_HASH, bot_token=BOT_TOKEN).send_message(ADMIN_ID, f"⚠️ User `{uid}` ရဲ့ String ပျက်သွားပါပြီ။")
                    break
                await asyncio.sleep(30)
    asyncio.create_task(run())

# --- ၄။ Expiry Checker (သက်တမ်းကုန်မကုန် စစ်ဆေးခြင်း) ---
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

# --- ၅။ Main API Bot Logic ---
async def main_bot():
    bot = Client("main_api_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    @bot.on_message(filters.command("start") & filters.private)
    async def start_handler(c, m):
        uid = m.from_user.id
        res = db.table("approved_users").select("*").eq("user_id", uid).execute()
        if res.data:
            db.table("user_states").upsert({"user_id": uid, "state": "awaiting_string"}).execute()
            await m.reply(f"✅ ဝန်ဆောင်မှုရှိပါသည်။ (Expiry: {res.data[0]['expiry_date']})\nအသုံးပြုရန် **String Session** ကို ပို့ပေးပါ။")
        else:
            kb = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("🛒 ဝယ်ယူရန်", url="https://t.me/Cambai138")]])
            await m.reply("❌ ဝန်ဆောင်မှု မဝယ်ရသေးပါ။ @Cambai138 ဆီမှာ အရင်ဝယ်ယူပါ။", reply_markup=kb)

    @bot.on_message(filters.command("add") & filters.user(ADMIN_ID))
    async def add_user(c, m):
        try:
            target_id = int(m.text.split()[1])
            kb = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("၁ လ", callback_data=f"dur_{target_id}_30")],
                [types.InlineKeyboardButton("Lifetime", callback_data=f"dur_{target_id}_9999")]
            ])
            await m.reply(f"👤 User: `{target_id}` အတွက် သက်တမ်းရွေးချယ်ပါ-", reply_markup=kb)
        except: await m.reply("Usage: `/add [ID]`")

    @bot.on_callback_query(filters.regex(r"^dur_"))
    async def set_duration(c, q):
        uid, days = int(q.data.split("_")[1]), int(q.data.split("_")[2])
        expiry = (datetime.now() + timedelta(days=days)).date().isoformat()
        db.table("approved_users").upsert({"user_id": uid, "expiry_date": expiry}).execute()
        await q.edit_message_text(f"✅ User `{uid}` အား ထည့်သွင်းပြီးပါပြီ။")
        try: await c.send_message(uid, "🎉 ဝန်ဆောင်မှု စတင်အသုံးပြုနိုင်ပါပြီ။ /start ကို နှိပ်ပါ။")
        except: pass

    @bot.on_message(filters.private & filters.text & ~filters.command(["start", "add"]))
    async def input_handler(c, m):
        uid = m.from_user.id
        state_res = db.table("user_states").select("state").eq("user_id", uid).execute()
        if not state_res.data: return
        state = state_res.data[0]['state']

        if state == "awaiting_string":
            db.table("pending_users").upsert({"user_id": uid, "string": m.text}).execute()
            db.table("user_states").update({"state": "awaiting_afk"}).eq("user_id", uid).execute()
            await m.reply("✅ String ရပါပြီ။ Offline ဖြစ်ရင် ပြန်ချင်တဲ့ **စာသား** ကို ပို့ပေးပါ။")
        
        elif state == "awaiting_afk":
            db.table("pending_users").update({"afk_text": m.text}).eq("user_id", uid).execute()
            db.table("user_states").update({"state": "submitted"}).eq("user_id", uid).execute()
            
            # Admin (သင့်ဆီ) သို့ ခွင့်ပြုချက်တောင်းရန် ပို့ခြင်း
            kb = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("✅ Accept (True)", callback_data=f"app_{uid}"),
                 types.InlineKeyboardButton("❌ Reject (False)", callback_data=f"rej_{uid}")]
            ])
            await bot.send_message(ADMIN_ID, f"🔔 **New Request**\nID: `{uid}`\nAFK Text: {m.text}", reply_markup=kb)
            await m.reply("⏳ Admin ဆီ ခွင့်ပြုချက် တောင်းခံထားပါသည်။")

    @bot.on_callback_query(filters.regex(r"^(app_|rej_)"))
    async def admin_decision(c, q):
        action, uid = q.data.split("_")[0], int(q.data.split("_")[1])
        if action == "app":
            data = db.table("pending_users").select("*").eq("user_id", uid).execute().data[0]
            db.table("approved_users").update({"string": data['string'], "afk_text": data['afk_text']}).eq("user_id", uid).execute()
            await start_userbot(uid, data['string'], data['afk_text'])
            await bot.send_message(uid, "🎉 Admin က အတည်ပြုလိုက်ပါပြီ။ Bot စတင် အလုပ်လုပ်ပါပြီ။")
            await q.edit_message_text(f"✅ Approved: {uid}")
        else:
            await bot.send_message(uid, "❌ Admin က သင့် Request ကို ငြင်းပယ်လိုက်ပါသည်။")
            await q.edit_message_text(f"❌ Rejected: {uid}")

    await bot.start()
    asyncio.create_task(expiry_checker(bot))
    await asyncio.Event().wait()

# --- ၆။ System Start ---
async def main():
    # Bot စတက်ချင်းမှာ Database ထဲက အဟောင်းတွေကို ပြန်နှိုးပေးခြင်း
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

