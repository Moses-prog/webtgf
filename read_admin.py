import codecs
with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with codecs.open('out.txt', 'w', encoding='utf-8') as out:
    for i, l in enumerate(lines):
        if 'elif data == "admin_features"' in l:
            out.write(''.join(lines[i:i+30]))
