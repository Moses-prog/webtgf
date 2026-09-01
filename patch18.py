with open('control_bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for l in lines:
    if l.startswith('                elif text:'):
        new_lines.append('        elif text:\n')
    elif "match = re.search(r't\\\\.me" in l:
        new_lines.append(l.replace('t\\\\.me', 't\.me').replace('(\\d+)', '(\d+)').replace('([^/\\?]+)', '([^/\?]+)'))
    else:
        new_lines.append(l)

with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(''.join(new_lines))
