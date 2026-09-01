import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_logic = '''        elif text:
            new_items = [x.strip() for x in text.split(',') if x.strip()]'''

new_logic = '''        elif text:
            new_items = []
            import re
            for x in text.split(','):
                x = x.strip()
                if not x: continue
                if "t.me/c/" in x:
                    match = re.search(r't\.me/c/(\d+)', x)
                    if match:
                        new_items.append(f"-100{match.group(1)}")
                        continue
                new_items.append(x)'''

if old_logic in c:
    c = c.replace(old_logic, new_logic)
else:
    print("WARNING: Could not find old_logic")

old_text1 = '''"*(Or manually reply with a @username or -100 ID)*\\n\\n"'''
new_text1 = '''"*(Or manually reply with a @username, -100 ID, or a private post link like https://t.me/c/1234...)*\\n\\n"'''
c = c.replace(old_text1, new_text1)

old_text2 = '''"*(Or manually reply with a comma-separated list of @username)*\\n\\n"'''
new_text2 = '''"*(Or manually reply with a comma-separated list of @username, -100 IDs, or https://t.me/c/... links)*\\n\\n"'''
c = c.replace(old_text2, new_text2)

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)