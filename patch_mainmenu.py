with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add to Main Menu
if 'Button.inline("🗑️ Deletion Suite", b"menu_deletion")' not in c:
    c = c.replace(
        '[Button.inline("🤖 AI Watermark Remover", b"menu_ai_watermark")],',
        '[Button.inline("🤖 AI Watermark Remover", b"menu_ai_watermark")],\n        [Button.inline("🗑️ Deletion Suite (Pro)", b"menu_deletion")],'
    )

with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("Main menu updated.")
