import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '[Button.inline("🖼 Image Branding", b"menu_image")' in line:
        lines[i] = '            [Button.inline("✨ Modification Rules", b"menu_modifications")],\n'
        lines[i+1] = '            [Button.inline("🚀 Auto-Posting Suite", b"menu_autoposting")],\n'
        lines[i+2] = '            [Button.inline("⚙️ Settings Panel", b"menu_settings")],\n'
        lines[i+3] = '            [Button.inline("🔌 Disconnect Account", b"disconnect_account")],\n'
        lines[i+4] = '            [Button.inline("💬 24/7 Support", b"menu_support"), Button.inline("ℹ️ About Us", b"menu_about")]\n'
        break

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(''.join(lines))
