import asyncio
from pyrogram import Client, filters
from supabase import create_client

# --- Configuration ---
SUPABASE_URL = "https://ljqlxbhcbtdvayjyrzfw.supabase.co"
SUPABASE_KEY = "EyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxqcWx4YmhjYnRkdmF5anlyemZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzMTYyNDcsImV4cCI6MjA4ODg5MjI0N30.oEt_8kWTzM_WBYBtJaFvqjnA6uvjL7uHiy4E5ASIymY"

# သင်ရထားတဲ့ String Session တွေကို ဒီ list ထဲမှာ အောက်ပါအတိုင်း စုထည့်ပါ
STRING_SESSIONS = [
    "BQJRNl4AGz9YFBS-7FamYgcMprgJFSQvLpyOU_y-sLyc4-mVftZZp-klJte8IvQIg1BZ1xCAYdFsI0ggD94yLeitUpx9H92lg1rakGNVYMMglWsRR4d7gTRQnrbtHk47W1groqFUuvkYXKxl0_r6IOQX9-eDc-HkC8tvZE2dVRmOOv-8vn_Ze8rPAVrrJsqo_IxokyEWmE7Ot8Ir7hh-8p8Bqo69ew7gNsYukQ6xO5xwOWAF6_VljjUebZEJmpq_mjNwmtxJCtNq5VH92TyH16bFpgx9WASVWUn9btSUFX6db3pojHQN7j2s6vzs2fbXrID-dv0TvhjZZw3JY5UhZiRSwXAaXQAAAAHNK5CbAA",
    # "နောက်ထပ် String Session များကို ဒီအောက်မှာ ဆက်ထည့်ပါ",
]

API_ID = 38876766
API_HASH = "e8d2d82f38704f4fcf171d3d35d3f811"

db = create_client(SUPABASE_URL, SUPABASE_KEY)

async def run_userbot(session_str, bot_num):
    try:
        async with Client(f"account_{bot_num}", session_string=session_str, api_id=API_ID, api_hash=API_HASH) as app:
            print(f"✅ Bot {bot_num} (Online!)")
            
            @app.on_message(filters.command("alive", prefixes=".") & filters.me)
            async def alive_cmd(_, message):
                await message.edit(f"🚀 Bot {bot_num} is running perfectly on Koyeb!")

            await asyncio.Event().wait()
    except Exception as e:
        print(f"❌ Bot {bot_num} error: {e}")

async def main():
    tasks = []
    for i, session in enumerate(STRING_SESSIONS, 1):
        tasks.append(run_userbot(session, i))
    
    if tasks:
        await asyncio.gather(*tasks)
    else:
        print("⚠️ String Session တစ်ခုမှ မရှိသေးပါ။")

if __name__ == "__main__":
    asyncio.run(main())

