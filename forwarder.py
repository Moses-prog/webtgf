import os
import asyncio
import re
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaWebPage
from telethon.sessions import StringSession

from database_manager import get_all_users, get_user_data

active_clients = {}

def apply_rules(text, user_data):
    if not text:
        return text
    
    # 1. Text Swaps
    swaps = user_data.get("text_swaps", {})
    for old_w, new_w in swaps.items():
        if old_w and new_w:
            text = re.sub(re.escape(old_w), new_w, text, flags=re.IGNORECASE)
            
    # 2. Replace Links
    link_replacement = user_data.get("replace_all_links_with", "").strip()
    if link_replacement:
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text = re.sub(url_pattern, link_replacement, text)

    # 3. Replace Usernames
    user_replacement = user_data.get("replace_all_usernames_with", "").strip()
    if user_replacement:
        username_pattern = r'@[\w_]+'
        text = re.sub(username_pattern, user_replacement, text)
        
    return text

async def handle_message(event, chat_id):
    user_data = get_user_data(chat_id)
    
    source_channels = user_data.get('sources', [])
    target_channels = user_data.get('targets', [])
    
    if not source_channels or not target_channels:
        return

    # Check if message is from a source
    is_source = False
    if str(event.chat_id) in source_channels:
        is_source = True
    elif hasattr(event, 'chat') and event.chat and hasattr(event.chat, 'username') and event.chat.username:
        if f"@{event.chat.username}" in source_channels or event.chat.username in source_channels:
            is_source = True
            
    if not is_source:
        return
        
    print(f"[Tenant {chat_id}] Received message from source: {event.chat_id}")
    
    modified_text = apply_rules(event.message.text, user_data)
    media_to_send = event.message.media
    
    if event.message.media:
        is_enabled = user_data.get("image_override_enabled", True)
        if is_enabled:
            image_swap_path = user_data.get("image_swap_path", "").strip()
            image_swap_url = user_data.get("image_swap_url", "").strip()
            
            if image_swap_path and os.path.exists(image_swap_path):
                media_to_send = image_swap_path
            elif image_swap_url:
                media_to_send = image_swap_url
            
    client = active_clients[chat_id]
    
    smart_delay = user_data.get("smart_delay_enabled", False)
    if smart_delay:
        import random
        # Wait between 1 to 3 minutes (60 to 180 seconds)
        delay_seconds = random.randint(60, 180)
        print(f"[Tenant {chat_id}] Smart Delay: Waiting {delay_seconds} seconds before forwarding...")
        await asyncio.sleep(delay_seconds)
    
    try:
        success = False
        if media_to_send and not isinstance(media_to_send, MessageMediaWebPage):
            for target in target_channels:
                await client.send_file(target, media_to_send, caption=modified_text)
                success = True
        else:
            if modified_text:
                for target in target_channels:
                    await client.send_message(target, modified_text, link_preview=True)
                    success = True
                    
        if success:
            import datetime
            from database_manager import get_stats, save_stats
            today = str(datetime.date.today())
            stats = get_stats()
            
            if stats.get("date") != today:
                stats["today"] = 0
                stats["date"] = today
                
            stats["total"] = stats.get("total", 0) + 1
            stats["today"] = stats.get("today", 0) + 1
            
            save_stats(stats)
                
    except Exception as e:
        print(f"[Tenant {chat_id}] Failed to forward cleanly: {e}")
        if modified_text:
            for target in target_channels:
                await client.send_message(target, modified_text)

async def monitor_users():
    print("Starting Multi-Tenant Forwarding Engine...")
    while True:
        try:
            # 1. Write the main heartbeat so the bot knows the engine is alive
            import time, json
            with open('status.json', 'w') as f:
                json.dump({"last_seen": time.time(), "status": "online"}, f)
                
            # 2. Check all tenants
            all_users = get_all_users()
            
            # Start new clients
            for chat_id in all_users:
                user_data = get_user_data(chat_id)
                session_str = user_data.get("session_string", "")
                
                if session_str and chat_id not in active_clients:
                    print(f"Booting Engine for Tenant {chat_id}...")
                    try:
                        api_id = user_data.get("api_id")
                        api_hash = user_data.get("api_hash")
                        client = TelegramClient(StringSession(session_str), api_id, api_hash)
                        await client.connect()
                        
                        # Use a lambda or partial to pass the chat_id into the event handler
                        client.add_event_handler(lambda e, cid=chat_id: handle_message(e, cid), events.NewMessage)
                        active_clients[chat_id] = client
                        print(f"✅ Engine ONLINE for Tenant {chat_id}")
                    except Exception as e:
                        print(f"❌ Failed to boot engine for {chat_id}: {e}")

            # Stop disconnected clients
            for chat_id in list(active_clients.keys()):
                user_data = get_user_data(chat_id)
                if not user_data.get("session_string"):
                    print(f"Shutting down Engine for Tenant {chat_id}...")
                    client = active_clients.pop(chat_id)
                    await client.disconnect()

        except Exception as e:
            print(f"Error in monitor loop: {e}")
            
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(monitor_users())
