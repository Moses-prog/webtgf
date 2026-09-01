import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add back handlers
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

idx = c.find('        elif data == "back":')
if idx == -1:
    idx = c.find('        if data == "back":')

if idx != -1:
    c = c[:idx] + back_handlers + '\n' + c[idx:]
else:
    print("WARNING: Could not find back handler")

# 2. Update Admin Panel to include Sleep Mode
admin_panel_old = '''        elif data == "admin_panel" and is_admin(chat_id):
            user_states[chat_id] = None
            tenants = get_tenants()
            
            buttons = [
                [Button.inline("👥 Manage Tenants", b"admin_tenants")],
                [Button.inline("👑 Pro Features (Locks)", b"admin_features")],
                [Button.inline("📢 Broadcast AI Update", b"admin_broadcast")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            
            await event.edit("👑 **Admin Panel**\\n\\nWelcome, Creator. What would you like to manage?", buttons=buttons)
            return'''

admin_features_old = '''        elif data == "admin_features" and is_admin(chat_id):
            toggles = get_feature_toggles()
            drip = toggles.get("drip_posting_unlocked", False)
            drip_text = "🟢 Drip Posting (Unlocked)" if drip else "🔴 Drip Posting (Locked)"
            
            buttons = [
                [Button.inline(drip_text, b"admin_toggle_drip")],
                [Button.inline("🔙 Back", b"admin_panel")]
            ]
            await event.edit("👑 **Pro Features**\\n\\nLock or unlock premium features for all tenants:", buttons=buttons)
            return
            
        elif data == "admin_toggle_drip" and is_admin(chat_id):
            toggles = get_feature_toggles()
            toggles["drip_posting_unlocked"] = not toggles.get("drip_posting_unlocked", False)
            save_feature_toggles(toggles)
            
            drip = toggles.get("drip_posting_unlocked", False)
            drip_text = "🟢 Drip Posting (Unlocked)" if drip else "🔴 Drip Posting (Locked)"
            
            buttons = [
                [Button.inline(drip_text, b"admin_toggle_drip")],
                [Button.inline("🔙 Back", b"admin_panel")]
            ]
            await event.edit("👑 **Pro Features**\\n\\nLock or unlock premium features for all tenants:", buttons=buttons)
            return'''
            
admin_features_new = '''        elif data == "admin_features" and is_admin(chat_id):
            toggles = get_feature_toggles()
            drip = toggles.get("drip_posting_unlocked", False)
            sleep = toggles.get("sleep_mode_unlocked", False)
            
            drip_text = "🟢 Drip Posting (Unlocked)" if drip else "🔴 Drip Posting (Locked)"
            sleep_text = "🟢 Sleep Mode (Unlocked)" if sleep else "🔴 Sleep Mode (Locked)"
            
            buttons = [
                [Button.inline(drip_text, b"admin_toggle_drip")],
                [Button.inline(sleep_text, b"admin_toggle_sleep")],
                [Button.inline("🔙 Back", b"admin_panel")]
            ]
            await event.edit("👑 **Pro Features**\\n\\nLock or unlock premium features for all tenants:", buttons=buttons)
            return
            
        elif data == "admin_toggle_drip" and is_admin(chat_id):
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
                [Button.inline("🔙 Back", b"admin_panel")]
            ]
            await event.edit("👑 **Pro Features**\\n\\nLock or unlock premium features for all tenants:", buttons=buttons)
            return
            
        elif data == "admin_toggle_sleep" and is_admin(chat_id):
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
                [Button.inline("🔙 Back", b"admin_panel")]
            ]
            await event.edit("👑 **Pro Features**\\n\\nLock or unlock premium features for all tenants:", buttons=buttons)
            return'''

if admin_features_old in c:
    c = c.replace(admin_features_old, admin_features_new)
else:
    print("WARNING: Could not find admin_features block")

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
    print("WARNING: Could not find menu_sleep block")

# 4. Replace b"back" with b"back_modifications" and b"back_autoposting"
def replace_back(marker, new_back):
    global c
    lines = c.split('\\n')
    in_block = False
    for i, line in enumerate(lines):
        if marker in line:
            in_block = True
        if in_block and ('b"back"' in line or 'b\\'back\\'' in line) and 'Button.inline' in line:
            lines[i] = line.replace('b"back"', f'b"{new_back}"').replace("b'back'", f'b"{new_back}"')
            break
    c = '\\n'.join(lines)

replace_back('elif data == "menu_image":', 'back_modifications')
replace_back('elif data == "menu_words":', 'back_modifications')
replace_back('elif data == "menu_links":', 'back_modifications')

replace_back('elif data == "menu_drip_posting":', 'back_autoposting')
replace_back('elif data == "menu_sleep":', 'back_autoposting')
replace_back('elif data == "sleep_toggle":', 'back_autoposting')
replace_back('elif data == "sleep_edit":', 'back_autoposting')
replace_back('elif data == "menu_queue":', 'back_autoposting')
replace_back('elif data == "queue_forward_all":', 'back_autoposting')
replace_back('elif data == "queue_clear":', 'back_autoposting')

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done patching.")
