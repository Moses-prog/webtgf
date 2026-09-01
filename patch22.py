with open('forwarder.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_boot = '''                    try:
                        api_id = user_data.get("api_id")
                        api_hash = user_data.get("api_hash")
                        client = TelegramClient(StringSession(session_str), api_id, api_hash)
                        await client.connect()
                        
                        # Use a lambda or partial to pass the chat_id into the event handler'''

new_boot = '''                    try:
                        api_id = user_data.get("api_id")
                        api_hash = user_data.get("api_hash")
                        client = TelegramClient(StringSession(session_str), api_id, api_hash)
                        await client.connect()
                        
                        # Populate entity cache to make -100 IDs work for both sources and targets
                        try:
                            print(f"[Tenant {chat_id}] Fetching dialogs to populate entity cache...")
                            await client.get_dialogs()
                        except Exception as e:
                            print(f"[Tenant {chat_id}] Failed to fetch dialogs: {e}")
                            
                        # Use a lambda or partial to pass the chat_id into the event handler'''

c = c.replace(old_boot, new_boot)

with open('forwarder.py', 'w', encoding='utf-8') as f:
    f.write(c)
