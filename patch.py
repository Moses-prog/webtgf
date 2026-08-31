import json
import os

with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add back_modifications and back_autoposting handlers
back_handlers = '''
        elif data == "back_modifications":
            user_states.pop(chat_id, None)
            text = "✨ **Modification Rules**\\n\\nConfigure how your forwarded messages are edited before they reach the target channels."
            buttons = [
                [Button.inline("🖼 Image Branding", b"menu_image"), Button.inline("✏️ Word Swapper", b"menu_words")],
                [Button.inline("🔗 Link & Branding", b"menu_links")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "back_autoposting":
            user_states.pop(chat_id, None)
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

idx = c.find('        if data == "back":')
if idx != -1:
    c = c[:idx] + back_handlers + '\n' + c[idx:]
else:
    print("Could not find back handler")

# 2. Update Admin Panel to include Sleep Mode
admin_panel_old = '''        elif data == "admin_panel":
            toggles = get_feature_toggles()
            drip = toggles.get("drip_posting_unlocked", False)
            drip_text = "🟢 Drip Posting (Unlocked)" if drip else "🔴 Drip Posting (Locked)"
            
            buttons = [
                [Button.inline(drip_text, b"admin_toggle_drip")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit("👑 **Admin Panel**\\n\\nLock or unlock premium features for all users:", buttons=buttons)
            return
            
        elif data == "admin_toggle_drip":
            toggles = get_feature_toggles()
            toggles["drip_posting_unlocked"] = not toggles.get("drip_posting_unlocked", False)
            save_feature_toggles(toggles)
            
            drip = toggles.get("drip_posting_unlocked", False)
            drip_text = "🟢 Drip Posting (Unlocked)" if drip else "🔴 Drip Posting (Locked)"
            
            buttons = [
                [Button.inline(drip_text, b"admin_toggle_drip")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit("👑 **Admin Panel**\\n\\nLock or unlock premium features for all users:", buttons=buttons)
            return'''

admin_panel_new = '''        elif data == "admin_panel":
            toggles = get_feature_toggles()
            drip = toggles.get("drip_posting_unlocked", False)
            sleep = toggles.get("sleep_mode_unlocked", False)
            
            drip_text = "🟢 Drip Posting (Unlocked)" if drip else "🔴 Drip Posting (Locked)"
            sleep_text = "🟢 Sleep Mode (Unlocked)" if sleep else "🔴 Sleep Mode (Locked)"
            
            buttons = [
                [Button.inline(drip_text, b"admin_toggle_drip")],
                [Button.inline(sleep_text, b"admin_toggle_sleep")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit("👑 **Admin Panel**\\n\\nLock or unlock premium features for all users:", buttons=buttons)
            return
            
        elif data == "admin_toggle_drip":
            toggles = get_feature_toggles()
            toggles["drip_posting_unlocked"] = not toggles.get("drip_posting_unlocked", False)
            save_feature_toggles(toggles)
            
            drip = toggles.get("drip_posting_unlocked", False)
            sleep = toggles.get("sleep_mode_unlocked", False)
            drip_text = "🟢 Drip Posting (Unlocked)" if drip else "🔴 Drip Posting (Locked)"
            sleep_text = "🟢 Sleep Mode (Unlocked)" if sleep else "🔴 Sleep Mode (Locked)"
            
            buttons = [
                [Button.inline(drip_text, b"admin_toggle_drip")],
                [Button.inline(sleep_text, b"admin_toggle_sleep")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit("👑 **Admin Panel**\\n\\nLock or unlock premium features for all users:", buttons=buttons)
            return
            
        elif data == "admin_toggle_sleep":
            toggles = get_feature_toggles()
            toggles["sleep_mode_unlocked"] = not toggles.get("sleep_mode_unlocked", False)
            save_feature_toggles(toggles)
            
            drip = toggles.get("drip_posting_unlocked", False)
            sleep = toggles.get("sleep_mode_unlocked", False)
            drip_text = "🟢 Drip Posting (Unlocked)" if drip else "🔴 Drip Posting (Locked)"
            sleep_text = "🟢 Sleep Mode (Unlocked)" if sleep else "🔴 Sleep Mode (Locked)"
            
            buttons = [
                [Button.inline(drip_text, b"admin_toggle_drip")],
                [Button.inline(sleep_text, b"admin_toggle_sleep")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit("👑 **Admin Panel**\\n\\nLock or unlock premium features for all users:", buttons=buttons)
            return'''

if admin_panel_old in c:
    c = c.replace(admin_panel_old, admin_panel_new)
else:
    print("Could not find admin panel block")

# 3. Add lock to menu_sleep
menu_sleep_old = '''        elif data == "menu_sleep":
            user_data = get_user_data(chat_id)'''
menu_sleep_new = '''        elif data == "menu_sleep":
            toggles = get_feature_toggles()
            if not toggles.get("sleep_mode_unlocked", False) and not is_admin(chat_id):
                await event.answer("👨‍🍳 Still cooking... This feature is locked by the Admin.", alert=True)
                return
            user_data = get_user_data(chat_id)'''

if menu_sleep_old in c:
    c = c.replace(menu_sleep_old, menu_sleep_new)
else:
    print("Could not find menu_sleep block")

# 4. Replace b"back" with b"back_modifications" in modification menus
def replace_back_in_block(code_str, marker, new_back):
    lines = code_str.split('\\n')
    in_block = False
    for i, line in enumerate(lines):
        if marker in line:
            in_block = True
        if in_block and 'b"back"' in line and 'Button.inline' in line:
            lines[i] = line.replace('b"back"', f'b"{new_back}"')
            in_block = False # only replace the first one in the block
    return '\\n'.join(lines)

c = replace_back_in_block(c, 'elif data == "menu_image":', 'back_modifications')
c = replace_back_in_block(c, 'elif data == "menu_words":', 'back_modifications')
c = replace_back_in_block(c, 'elif data == "menu_links":', 'back_modifications')

# 5. Replace b"back" with b"back_autoposting" in autoposting menus
c = replace_back_in_block(c, 'elif data == "menu_drip_posting":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "menu_sleep":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "sleep_toggle":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "sleep_edit":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "menu_queue":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "queue_forward_all":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "queue_clear":', 'back_autoposting')


with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done!')
