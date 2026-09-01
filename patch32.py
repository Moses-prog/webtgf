with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(r't\.me/c/(\\d+)', r't\.me/c/(\d+)')
c = c.replace(r't\.me/([^/\\?]+)', r't\.me/([^/\?]+)')

with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
