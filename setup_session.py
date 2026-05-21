"""
Run this ONCE locally to create Telegram session.
Then upload session to GitHub Secrets as SESSION_BASE64.
"""
import asyncio
import base64
from telethon import TelegramClient
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, SESSION_NAME


async def main():
    print("🔐 Creating Telegram session...")
    print("You will receive a code in Telegram/SMS\n")

    client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start(phone=TELEGRAM_PHONE)

    me = await client.get_me()
    print(f"\n✅ Authorized as: {me.first_name} (@{me.username})")

    await client.disconnect()

    # Encode session to base64
    session_file = f"{SESSION_NAME}.session"
    with open(session_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    print("\n" + "="*60)
    print("📋 Copy this value to GitHub Secret 'SESSION_BASE64':")
    print("="*60)
    print(encoded)
    print("="*60)
    print("\nGo to: GitHub repo → Settings → Secrets → New secret")
    print("Name: SESSION_BASE64")
    print("Value: (paste the long string above)")


if __name__ == "__main__":
    asyncio.run(main())
