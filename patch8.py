with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace(')\\n        elif data == "admin_ai_broadcast"', ')\n        elif data == "admin_ai_broadcast"')
with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
