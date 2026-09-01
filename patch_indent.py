import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('                  elif data == "menu_sleep":', '        elif data == "menu_sleep":')

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
