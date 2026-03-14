import os
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from supabase import create_client
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import telebot
from telebot import types

# --- Config (သားကြီးပေးထားတဲ့အတိုင်း) ---
ADMIN_ID = 7737151643
BOT_TOKEN = "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A"
SUPABASE_URL = "https://xslvzwfizcvdbjckpsem.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzbHZ6d2ZpemN2ZGJqY2twc2VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzODc3ODYsImV4cCI6MjA4ODk2Mzc4Nn0.DC-XWrqBGno4vnWFPP2cPqBMG0zB-LEeKP7Hv6VPnc4"
API_ID = 38876766
API_HASH = "e8d2d82f38704f4fcf171d3d35d3f811"

# --- Render Port Binding (Flask မပါဘဲ အရှင်းဆုံးနည်း) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"AFK BOT IS ALIVE")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- Setup Bot & DB ---
bot = telebot.TeleBot(BOT_TOKEN)
db = create_client(SUPABASE_URL, SUPABASE_KEY)
logging.basicConfig(level=logging.INFO)

# --- AFK Logic ---
async def start_user_afk(uid, session, afk_text):
    try:
        client = TelegramClient(StringSession(session), API_ID, API_HASH)
        await client.start()
        
        @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def handler(event):
            me = await client.get_me()
            # User က offline ဖြစ်နေမှ စာပြန်မည်
            if hasattr(me.status, 'was_online') or me.status is None:
                await event.reply(afk_text)
        await client.run_until_disconnected()
    except: pass

# --- Bot Commands (Admin Panel အပြည့်အစုံ) ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    res = db.table("approved_users").select("*").eq("user_id", uid).execute()
    
    if res.data:
        bot.send_message(uid, "✅ အသုံးပြုခွင့်ရှိပါသည်။ String Session နှင့် AFK စာသား ပို့ပေးပါ။")
    else:
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = [
            types.InlineKeyboardButton("1 လ ✅", callback_data=f"acc_{uid}_1m"),
            types.InlineKeyboardButton("2 လ ✅", callback_data=f"acc_{uid}_2m"),
            types.InlineKeyboardButton("5 လ ✅", callback_data=f"acc_{uid}_5m"),
            types.InlineKeyboardButton("7 လ ✅", callback_data=f"acc_{uid}_7m"),
            types.InlineKeyboardButton("1 နှစ် ✅", callback_data=f"acc_{uid}_1y"),
            types.InlineKeyboardButton("ငြင်းပယ် ❌", callback_data=f"rej_{uid}")
        ]
        kb.add(*btns)
        bot.send_message(ADMIN_ID, f"🔔 တောင်းဆိုမှုသစ်:\nUser: @{m.from_user.username}\nID: `{uid}`", reply_markup=kb)
        bot.send_message(uid, "⏳ Admin ဆီမှ အသုံးပြုခွင့် တောင်းဆိုထားပါသည်။ ခဏစောင့်ပါ။")

@bot.callback_query_handler(func=lambda q: True)
def admin_cb(q):
    data = q.data.split("_")
    action, uid = data[0], int(data[1])
    if action == "acc":
        dur = data[2]
        db.table("approved_users").upsert({"user_id": uid, "status": "active"}).execute()
        bot.send_message(uid, f"🎉 Admin က ခွင့်ပြုလိုက်ပါပြီ။ ({dur}) သုံးစွဲနိုင်ပါသည်။")
    elif action == "rej":
        bot.send_message(uid, "❌ Admin @Cambai138 ဆီမှ အသုံးပြုခွင့် မဝယ်ရသေးပါ။")
    bot.answer_callback_query(q.id)

# --- Main Engine ---
async def main():
    # Render အတွက် Port နိုးမယ်
    Thread(target=run_health_server, daemon=True).start()
    
    # DB က User တွေ ပြန်နှိုးမယ်
    try:
        users = db.table("approved_users").select("*").execute().data
        for u in users:
            if u.get('string') and u.get('afk_text'):
                asyncio.create_task(start_user_afk(u['user_id'], u['string'], u['afk_text']))
    except: pass

    # Bot Polling
    bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
