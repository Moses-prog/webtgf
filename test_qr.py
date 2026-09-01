import asyncio
from telethon import TelegramClient

async def test():
    client = TelegramClient("anon", 6, "eb06d4abfb49dc3eeb1aeb98ae0f581e")
    await client.connect()
    print("Connected")
    qr = await client.qr_login()
    print("QR URL:", qr.url)
    print("Waiting...")
    try:
        await qr.wait(10)
        print("Done!")
    except Exception as e:
        print("Error:", repr(e))
    await client.disconnect()

asyncio.run(test())
