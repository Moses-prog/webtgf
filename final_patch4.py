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
    c = c[:idx] + back_handlers + '\\n' + c[idx:]
else:
    print("WARNING: Could not find back handler")

# 2. Update Admin Panel to include Sleep Mode
admin_features_old = '''        elif data == "admin_features" and is_admin(chat_id):
            toggles = get_feature_toggles()
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\\n\\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )'''

admin_features_new = '''        elif data == "admin_features" and is_admin(chat_id):
            toggles = get_feature_toggles()
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            sleep_locked = not toggles.get("sleep_mode_unlocked", False)
            
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            sleep_btn_text = "🔓 Unlock Sleep Mode" if sleep_locked else "🔒 Lock Sleep Mode"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\\n\\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline(sleep_btn_text, b"toggle_admin_sleep")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )'''

if admin_features_old in c:
    c = c.replace(admin_features_old, admin_features_new)
else:
    print("WARNING: Could not find admin_features block")

# 3. Update toggle_admin_drip to include sleep toggle in its UI refresh
toggle_admin_drip_old = '''        elif data == "toggle_admin_drip" and is_admin(chat_id):
            toggles = get_feature_toggles()
            toggles["drip_posting_unlocked"] = not toggles.get("drip_posting_unlocked", False)
            save_feature_toggles(toggles)
            
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\\n\\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )'''

toggle_admin_drip_new = '''        elif data == "toggle_admin_drip" and is_admin(chat_id):
            toggles = get_feature_toggles()
            toggles["drip_posting_unlocked"] = not toggles.get("drip_posting_unlocked", False)
            save_feature_toggles(toggles)
            
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            sleep_locked = not toggles.get("sleep_mode_unlocked", False)
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            sleep_btn_text = "🔓 Unlock Sleep Mode" if sleep_locked else "🔒 Lock Sleep Mode"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\\n\\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline(sleep_btn_text, b"toggle_admin_sleep")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )'''

if toggle_admin_drip_old in c:
    c = c.replace(toggle_admin_drip_old, toggle_admin_drip_new)
else:
    print("WARNING: Could not find toggle_admin_drip block")

# 4. Update toggle_admin_ai to include sleep toggle in its UI refresh
toggle_admin_ai_old = '''        elif data == "toggle_admin_ai" and is_admin(chat_id):
            toggles = get_feature_toggles()
            toggles["ai_watermark_unlocked"] = not toggles.get("ai_watermark_unlocked", False)
            save_feature_toggles(toggles)
            
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\\n\\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )'''

toggle_admin_ai_new = '''        elif data == "toggle_admin_ai" and is_admin(chat_id):
            toggles = get_feature_toggles()
            toggles["ai_watermark_unlocked"] = not toggles.get("ai_watermark_unlocked", False)
            save_feature_toggles(toggles)
            
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            sleep_locked = not toggles.get("sleep_mode_unlocked", False)
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            sleep_btn_text = "🔓 Unlock Sleep Mode" if sleep_locked else "🔒 Lock Sleep Mode"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\\n\\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline(sleep_btn_text, b"toggle_admin_sleep")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )
            
        elif data == "toggle_admin_sleep" and is_admin(chat_id):
            toggles = get_feature_toggles()
            toggles["sleep_mode_unlocked"] = not toggles.get("sleep_mode_unlocked", False)
            save_feature_toggles(toggles)
            
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            sleep_locked = not toggles.get("sleep_mode_unlocked", False)
            
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            sleep_btn_text = "🔓 Unlock Sleep Mode" if sleep_locked else "🔒 Lock Sleep Mode"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\\n\\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline(sleep_btn_text, b"toggle_admin_sleep")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )'''

if toggle_admin_ai_old in c:
    c = c.replace(toggle_admin_ai_old, toggle_admin_ai_new)
else:
    print("WARNING: Could not find toggle_admin_ai block")

# 5. Add lock to menu_sleep
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

# 6. Replace back buttons in specific sub-menus
def replace_back_in_block(code_str, marker, new_back):
    lines = code_str.split('\\n')
    in_block = False
    for i, line in enumerate(lines):
        if marker in line:
            in_block = True
        if in_block and ('b"back"' in line or 'b\\'back\\'' in line) and 'Button.inline' in line:
            lines[i] = line.replace('b"back"', f'b"{new_back}"').replace("b'back'", f'b"{new_back}"')
            in_block = False # only replace the first one found in this block
    return '\\n'.join(lines)

c = replace_back_in_block(c, 'elif data == "menu_image":', 'back_modifications')
c = replace_back_in_block(c, 'elif data == "menu_words":', 'back_modifications')
c = replace_back_in_block(c, 'elif data == "menu_links":', 'back_modifications')

c = replace_back_in_block(c, 'elif data == "menu_drip_posting":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "menu_sleep":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "sleep_toggle":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "sleep_edit":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "menu_queue":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "queue_forward_all":', 'back_autoposting')
c = replace_back_in_block(c, 'elif data == "queue_clear":', 'back_autoposting')

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done patching.")