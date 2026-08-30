import re

with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update get_main_keyboard
old_menu = '''        else:
            buttons.extend([
                [Button.inline(f"📌 Sources ({len(sources)})", b"menu_sources"), Button.inline(f"🎯 Targets ({len(targets)})", b"menu_targets")],
                [Button.inline("🖼 Image Branding", b"menu_image"), Button.inline("✏️ Word Swapper", b"menu_words")],
                [Button.inline("🔗 Link & Branding", b"menu_links"), Button.inline("⚙️ Settings Panel", b"menu_settings")],
                [Button.inline("🕐 Drip Posting", b"menu_drip_posting"), Button.inline("💤 Sleep Mode", b"menu_sleep")],
                [Button.inline("📥 View Queue", b"menu_queue")],
                [Button.inline("🔌 Disconnect Account", b"disconnect_account")],
                [Button.inline("💬 24/7 Support", b"menu_support"), Button.inline("ℹ️ About Us", b"menu_about")]
            ])'''
new_menu = '''        else:
            buttons.extend([
                [Button.inline(f"📌 Sources ({len(sources)})", b"menu_sources"), Button.inline(f"🎯 Targets ({len(targets)})", b"menu_targets")],
                [Button.inline("✨ Modification Rules", b"menu_modifications")],
                [Button.inline("🚀 Auto-Posting Suite", b"menu_autoposting")],
                [Button.inline("⚙️ Settings Panel", b"menu_settings")],
                [Button.inline("🔌 Disconnect Account", b"disconnect_account")],
                [Button.inline("💬 24/7 Support", b"menu_support"), Button.inline("ℹ️ About Us", b"menu_about")]
            ])'''

c = c.replace(old_menu, new_menu)

# 2. Add the sub-menus
submenu_code = '''
        elif data == "menu_modifications":
            text = "✨ **Modification Rules**\\n\\nConfigure how your forwarded messages are edited before they reach the target channels."
            buttons = [
                [Button.inline("🖼 Image Branding", b"menu_image"), Button.inline("✏️ Word Swapper", b"menu_words")],
                [Button.inline("🔗 Link & Branding", b"menu_links")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "menu_autoposting":
            user_data = get_user_data(chat_id)
            queue_len = len(user_data.get("drip_queue", []))
            text = f"🚀 **Auto-Posting Suite**\\n\\nControl the flow of your messages.\\n\\n**Messages in Queue:** {queue_len}"
            buttons = [
                [Button.inline("🕐 Drip Posting", b"menu_drip_posting"), Button.inline("💤 Sleep Mode", b"menu_sleep")],
                [Button.inline(f"📥 View Queue ({queue_len})", b"menu_queue")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return
'''

idx = c.find('        elif data == "menu_drip_posting":')
if idx != -1:
    c = c[:idx] + submenu_code + '\n' + c[idx:]
else:
    print("Could not find menu_drip_posting")

with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
