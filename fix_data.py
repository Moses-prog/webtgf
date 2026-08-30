with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re
c = re.sub(r'elif data == b"([^"]+)":', r'elif data == "\1":', c)

with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
