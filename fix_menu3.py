import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '            [Button.inline("🔌 Disconnect Account", b"disconnect_account")],\n' == line:
        # Check if the next line is 24/7 support
        if 'menu_support' in lines[i+1] and 'menu_support' in lines[i+2]:
            # Delete line i+2
            lines.pop(i+2)
        break

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(''.join(lines))
