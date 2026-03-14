import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from supabase import create_client
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import telebot

# --- Setup ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8731265744:AAGGaLhfxWZlMwRihJd254Sl_ItnU5sbF6A"
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_ID = int(os.environ.get("API_ID", 38876766))
API_HASH = os.environ.get("API_HASH", "e8d2d82f38704f4fcf171d3d35d3f811")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
running_clients = {}

@app.route('/')
def home(): return "SYSTEM ONLINE", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- AFK Client Function ---
async def start_afk_client(uid, session_str, afk_text):
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.start()
        running_clients[uid] = client
        
        @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def handler(event):
            me = await client.get_me()
            # Status စစ်ဆေးခြင်း
            if hasattr(me.status, 'was_online') or me.status is None:
                await event.reply(afk_text)
        
        logging.info(f"✅ User {uid} is now AFK protected.")
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"❌ Client {uid} Error: {e}")

# --- Bot Commands ---
@bot.message_handler(commands=['start'])
def welcome(m):
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    res = db.table("approved_users").select("*").eq("user_id", m.chat.id).execute()
    if res.data:
        bot.reply_to(m, "✅ ဝန်ဆောင်မှုရှိပါသည်။ String Session ပို့ပေးပါ။")
    else:
        bot.reply_to(m, "❌ ဝယ်ယူရန် Admin @Cambai138 ကို ဆက်သွယ်ပါ။")

# --- Main Run ---
async def main():
    # ၁။ Flask ကို Thread နဲ့ နိုးမယ်
    Thread(target=run_flask, daemon=True).start()
    
    # ၂။ Database က User တွေကို ပြန်နှိုးမယ်
    try:
        db = create_client(SUPABASE_URL, SUPABASE_KEY)
        users = db.table("approved_users").select("*").execute().data
        for u in users:
            if u.get('string') and u.get('afk_text'):
                asyncio.create_task(start_afk_client(u['user_id'], u['string'], u['afk_text']))
    except: pass

    # ၃။ Main Bot ကို Polling လုပ်မယ်
    logging.info("🚀 Bot is starting...")
    bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
