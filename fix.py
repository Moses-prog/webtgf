import re
with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix broken newlines in string literals
c = re.sub(r'\"\s*\n\s*\n\"', r'\\n\\n"', c)
c = re.sub(r'\"\s*\n\"', r'\\n"', c)

# Let's just fix it by replacing the whole broken block!
