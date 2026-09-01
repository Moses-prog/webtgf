with open('forwarder.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_logic = '''async def handle_message(event, chat_id):
    from database_manager import save_user_data
    user_data = get_user_data(chat_id)'''

new_logic = '''async def handle_message(event, chat_id):
    print(f"[DEBUG-ALL-MESSAGES] Tenant {chat_id} received message from {event.chat_id}")
    from database_manager import save_user_data
    user_data = get_user_data(chat_id)'''

if old_logic in c:
    c = c.replace(old_logic, new_logic)
    with open('forwarder.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Debug log injected.")
else:
    print("Could not find block.")
