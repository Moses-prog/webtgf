with open('control_bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('out.txt', 'w', encoding='utf-8') as f:
    f.writelines(lines[45:65])
    f.write('\n\n---\n\n')
    f.writelines(lines[510:530])
