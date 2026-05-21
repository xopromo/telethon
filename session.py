import asyncio
import base64
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
PHONE = "+79952230812"
SESSION = "tg_session"

async def main():
    print("Connecting to Telegram...")
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start(phone=PHONE)
    me = await client.get_me()
    print(f"Success! Logged in as: {me.first_name}")
    await client.disconnect()

    with open(f"{SESSION}.session", "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    print("\n--- Copy this to GitHub Secret SESSION_BASE64 ---")
    print(encoded)
    print("---------------------------------------------------")

asyncio.run(main())
