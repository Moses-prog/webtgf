with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_handler = '''@bot.on(events.NewMessage(pattern='/admin_logs'))
async def admin_logs_handler(event):
    chat_id = event.chat_id
    if not is_admin(chat_id):
        return
        
    try:
        with open('forwarder.log', 'r', encoding='utf-8') as log_file:
            logs = log_file.readlines()[-30:]
            log_text = "".join(logs)
            if not log_text:
                await event.respond("Logs are empty.")
            else:
                await event.respond(f"**Latest Logs:**\\n{log_text[-3500:]}")
    except Exception as e:
        await event.respond(f"Failed to read logs: {e}")
'''

# append it just before ot.run_until_disconnected()
if 'bot.run_until_disconnected()' in c:
    c = c.replace('bot.run_until_disconnected()', new_handler + '\nbot.run_until_disconnected()')
    with open('control_bot.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Added /admin_logs handler.")
else:
    print("Could not find bot.run_until_disconnected")
