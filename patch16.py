import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_block = '''        elif text:
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

new_block = '''        elif text:
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
                elif "t.me/" in x:
                    match = re.search(r't\.me/([^/\?]+)', x)
                    if match:
                        username = match.group(1)
                        if username not in ["c", "joinchat", "+"]:
                            new_items.append(f"@{username}")
                            continue
                new_items.append(x)'''

if old_block in c:
    c = c.replace(old_block, new_block)
else:
    print("WARNING: Could not find old_block")

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Link parser updated.")