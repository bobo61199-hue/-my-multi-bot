import os, asyncio, logging, requests, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from supabase import create_client
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import UserStatusOnline
import telebot
from telebot import types

# --- Config (သားကြီးရဲ့ ID တွေ သေချာပြန်စစ်ပါ) ---
ADMIN_ID = 7737151643
BOT_TOKEN = "8731265744:AAErBFmUgRj2jDJdYS-izEvkSxPou3GrNkU"
SUPABASE_URL = "https://xslvzwfizcvdbjckpsem.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzbHZ6d2ZpemN2ZGJqY2twc2VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzODc3ODYsImV4cCI6MjA4ODk2Mzc4Nn0.DC-XWrqBGno4vnWFPP2cPqBMG0zB-LEeKP7Hv6VPnc4"
API_ID = 38876766
API_HASH = "e8d2d82f38704f4fcf171d3d35d3f811"
RENDER_URL = "https://my-multi-bot-q4d0.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
db = create_client(SUPABASE_URL, SUPABASE_KEY)
logging.basicConfig(level=logging.INFO)

# --- AFK Userbot Logic ---
async def start_user_afk(uid, session, afk_text):
    try:
        client = TelegramClient(StringSession(session), API_ID, API_HASH)
        await client.start()
        @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def handler(event):
            me = await client.get_me()
            # User Online မဖြစ်မှသာ Reply ပို့မည်
            if not isinstance(me.status, UserStatusOnline):
                await event.reply(afk_text)
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"Userbot Error for {uid}: {e}")

# --- Bot Commands ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    uname = f"@{m.from_user.username}" if m.from_user.username else f"ID: {uid}"
    
    # User အခြေအနေကို DB မှာ အရင်စစ်မယ်
    res = db.table("approved_users").select("*").eq("user_id", uid).execute()
    
    if res.data and res.data[0].get('status') == 'active':
        bot.send_message(uid, "✅ သင့်မှာ အသုံးပြုခွင့်ရှိပြီးသားပါ။ String Session အရင်ပို့ပေးပါ။")
    else:
        # Admin ဆီကို ခလုတ်တွေနဲ့ စာပို့မယ်
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = [
            types.InlineKeyboardButton("1 လ ✅", callback_data=f"acc_{uid}_1လ"),
            types.InlineKeyboardButton("3 လ ✅", callback_data=f"acc_{uid}_3လ"),
            types.InlineKeyboardButton("6 လ ✅", callback_data=f"acc_{uid}_6လ"),
            types.InlineKeyboardButton("1 နှစ် ✅", callback_data=f"acc_{uid}_1နှစ်"),
            types.InlineKeyboardButton("ငြင်းပယ် ❌", callback_data=f"rej_{uid}")
        ]
        kb.add(*btns)
        bot.send_message(ADMIN_ID, f"🔔 တောင်းဆိုမှုသစ်:\nUser: {uname}\nID: `{uid}`", reply_markup=kb)
        bot.send_message(uid, "⏳ Admin ဆီမှ အသုံးပြုခွင့် တောင်းဆိုထားပါသည်။ ခဏစောင့်ပါ။")

@bot.callback_query_handler(func=lambda q: True)
def admin_cb(q):
    data = q.data.split("_")
    action, uid = data[0], int(data[1])
    
    if action == "acc":
        dur = data[2]
        # DB မှာ Status ကို active လုပ်မယ်
        db.table("approved_users").upsert({"user_id": uid, "status": "active", "duration": dur}).execute()
        bot.send_message(uid, f"🎉 Admin မှ သုံးခွင့် {dur} ပေးထားပါတယ်\n\nအကောင့်ဝင်ဖို့အတွက် **String Session** ကို ပို့ပေးပါ။")
        bot.edit_message_text(f"✅ User {uid} ကို {dur} ပေးလိုက်ပြီ။", q.message.chat.id, q.message.message_id)
        
    elif action == "rej":
        bot.send_message(uid, "❌ @Cambai138 ဆီမှာ service မဝယ်ရသေးပါလို့။")
        bot.edit_message_text(f"❌ User {uid} ကို ငြင်းပယ်လိုက်ပြီ။", q.message.chat.id, q.message.message_id)
    bot.answer_callback_query(q.id)

@bot.message_handler(func=lambda m: True)
def handle_input(m):
    uid = m.from_user.id
    res = db.table("approved_users").select("*").eq("user_id", uid).execute()
    if not res.data or res.data[0].get('status') != 'active': return

    if len(m.text) > 100: # String Session
        db.table("approved_users").update({"string": m.text}).eq("user_id", uid).execute()
        bot.reply_to(m, "✅ String မှတ်ပြီးပြီ။ AFK ဖြစ်နေချိန် ပြန်ချင်တဲ့စာသား (Auto-reply) ကို ပို့ပေးပါ။")
    else: # AFK Text
        db.table("approved_users").update({"afk_text": m.text}).eq("user_id", uid).execute()
        bot.reply_to(m, "🚀 စနစ်အားလုံး အဆင်သင့်ဖြစ်ပါပြီ။ Online မရှိချိန်မှာ Bot က အလိုအလျောက် ပြန်ပေးပါလိမ့်မယ်။")
        row = res.data[0]
        if row.get('string'):
             asyncio.run_coroutine_threadsafe(start_user_afk(uid, row['string'], m.text), main_loop)

# --- Keep-Alive System ---
def keep_alive():
    while True:
        try: requests.get(RENDER_URL, timeout=10)
        except: pass
        time.sleep(300)

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), lambda *args: None).serve_forever()

if __name__ == "__main__":
    Thread(target=run_health_server, daemon=True).start()
    Thread(target=keep_alive, daemon=True).start()
    main_loop = asyncio.new_event_loop()
    Thread(target=main_loop.run_forever, daemon=True).start()
    
    # 409 Conflict ရှင်းဖို့
    bot.delete_webhook()
    bot.infinity_polling()
