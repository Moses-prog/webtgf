with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_block = '''        elif text:
            new_items = []
            import re
            for x in text.split(','):
                x = x.strip()
                if not x: continue
                if "t.me/c/" in x:
                    match = re.search(r't\\\\.me/c/(\\\\d+)', x)
                    if match:
                        new_items.append(f"-100{match.group(1)}")
                        continue
                elif "t.me/" in x:
                    match = re.search(r't\\\\.me/([^/\\\\?]+)', x)
                    if match:
                        username = match.group(1)
                        if username not in ["c", "joinchat", "+"]:
                            new_items.append(f"@{username}")
                            continue
                new_items.append(x)'''

old_block_search = c[c.find('elif text:'):]
old_block_search = old_block_search[:old_block_search.find('if not new_items:')]

if 'elif text:' in old_block_search:
    c = c.replace(old_block_search, new_block + '\n        ')
    with open('control_bot.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Replaced')
