import asyncio
import os
import requests
import time
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from supabase import create_client

# --- Flask Server (Render အတွက် Port ဖွင့်ပေးရန်) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run_flask():
    # Render ရဲ့ Dynamic Port ကို ဖတ်ရန်
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- Keep Alive Loop (Bot ကိုယ်တိုင် ပြန် Ping ရန်) ---
def keep_alive():
    # ဒီနေရာမှာ သင် Render မှာ Deploy ပြီးရင်ရလာမယ့် URL ကို ထည့်ပေးရပါမယ်
    # ဥပမာ - https://your-bot-name.onrender.com
    RENDER_URL = "သင်၏_Render_URL_ကိုဒီမှာထည့်ပါ" 
    while True:
        try:
            requests.get(RENDER_URL)
            print("Pinged self to stay awake!")
        except:
            pass
        time.sleep(600) # ၁၀ မိနစ်တစ်ခါ Ping မည်

# --- Configuration ---
SUPABASE_URL = "https://ljqlxbhcbtdvayjyrzfw.supabase.co"
SUPABASE_KEY = "EyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxqcWx4YmhjYnRkdmF5anlyemZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzMTYyNDcsImV4cCI6MjA4ODg5MjI0N30.oEt_8kWTzM_WBYBtJaFvqjnA6uvjL7uHiy4E5ASIymY"

STRING_SESSIONS = [
    "BQJRNl4AGz9YFBS-7FamYgcMprgJFSQvLpyOU_y-sLyc4-mVftZZp-klJte8IvQIg1BZ1xCAYdFsI0ggD94yLeitUpx9H92lg1rakGNVYMMglWsRR4d7gTRQnrbtHk47W1groqFUuvkYXKxl0_r6IOQX9-eDc-HkC8tvZE2dVRmOOv-8vn_Ze8rPAVrrJsqo_IxokyEWmE7Ot8Ir7hh-8p8Bqo69ew7gNsYukQ6xO5xwOWAF6_VljjUebZEJmpq_mjNwmtxJCtNq5VH92TyH16bFpgx9WASVWUn9btSUFX6db3pojHQN7j2s6vzs2fbXrID-dv0TvhjZZw3JY5UhZiRSwXAaXQAAAAHNK5CbAA",
    # အခြား String များကို ဤအောက်တွင် ဆက်ထည့်ပါ
]

API_ID = 38876766
API_HASH = "e8d2d82f38704f4fcf171d3d35d3f811"

async def run_userbot(session_str, bot_num):
    try:
        async with Client(f"acc_{bot_num}", session_string=session_str, api_id=API_ID, api_hash=API_HASH) as app:
            print(f"✅ Bot {bot_num} is Online!")
            await asyncio.Event().wait()
    except Exception as e:
        print(f"❌ Bot {bot_num} error: {e}")

async def main_async():
    tasks = [run_userbot(s, i) for i, s in enumerate(STRING_SESSIONS, 1)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Flask ကို Thread တစ်ခုနဲ့ သီးသန့် Run မည်
    Thread(target=run_flask).start()
    # Keep Alive ကို Thread တစ်ခုနဲ့ Run မည်
    Thread(target=keep_alive).start()
    # Bot Main Loop ကို Run မည်
    asyncio.run(main_async())
