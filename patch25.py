import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_command = '''    # ADMIN LOGS COMMAND
    if text == "/admin_logs" and is_admin(chat_id):
        try:
            with open('forwarder.log', 'r') as log_file:
                logs = log_file.readlines()[-30:]
                log_text = "".join(logs)
                if not log_text:
                    await event.respond("Logs are empty.")
                else:
                    await event.respond(f"**Latest Logs:**\\n{log_text[-4000:]}")
        except Exception as e:
            await event.respond(f"Failed to read logs: {e}")
        return'''

# find where to inject it
target = '''    if text == "/start":'''
c = c.replace(target, new_command + '\n\n' + target)

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
