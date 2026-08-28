import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

if not API_ID or not API_HASH:
    print("Please set API_ID and API_HASH in your .env file.")
    exit(1)

print("Starting session generator...")
with TelegramClient(StringSession(), int(API_ID), API_HASH) as client:
    print("\n--- YOUR STRING SESSION ---")
    print(client.session.save())
    print("---------------------------\n")
    print("Copy the string above and save it as SESSION_STRING in your .env file.")
