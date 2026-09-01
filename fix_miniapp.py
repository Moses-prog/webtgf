with open('web.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Extract the miniapp route block
import re
match = re.search(r"(@app\.route\('/miniapp'\).*?return html\n)", c, re.DOTALL)
if not match:
    print("Could not find miniapp route")
else:
    miniapp_block = match.group(1)
    # Remove it from current position
    c = c.replace(miniapp_block, '')
    # Insert it just before app.run
    c = c.replace("if __name__", miniapp_block + "\nif __name__")
    with open('web.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Moved miniapp route to correct position.")
