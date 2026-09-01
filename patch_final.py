import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

def replace_back_safe(code, marker, new_back):
    lines = code.split('\n')
    in_block = False
    for i, line in enumerate(lines):
        if marker in line:
            in_block = True
        if in_block and ('b"back"' in line or "b'back'" in line) and 'Button.inline' in line:
            lines[i] = line.replace('b"back"', f'b"{new_back}"').replace("b'back'", f'b"{new_back}"')
            in_block = False
    return '\n'.join(lines)

c = replace_back_safe(c, 'elif data == "menu_image":', 'back_modifications')
c = replace_back_safe(c, 'elif data == "menu_words":', 'back_modifications')
c = replace_back_safe(c, 'elif data == "menu_links":', 'back_modifications')
c = replace_back_safe(c, 'elif data == "menu_drip_posting":', 'back_autoposting')

# 3. Update Admin Features Block to include Sleep Mode
admin_features_old = '''        elif data == "admin_features" and is_admin(chat_id):
            toggles = get_feature_toggles()
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\n\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )
            
        elif data == "toggle_admin_drip" and is_admin(chat_id):
            toggles = get_feature_toggles()
            toggles["drip_posting_unlocked"] = not toggles.get("drip_posting_unlocked", False)
            save_feature_toggles(toggles)
            
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\n\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )
            
        elif data == "toggle_admin_ai" and is_admin(chat_id):
            toggles = get_feature_toggles()
            toggles["ai_watermark_unlocked"] = not toggles.get("ai_watermark_unlocked", False)
            save_feature_toggles(toggles)
            
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\n\nLock or unlock features for all tenants.",
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
                "🎛️ **Admin Feature Toggles**\n\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline(sleep_btn_text, b"toggle_admin_sleep")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )
            
        elif data == "toggle_admin_drip" and is_admin(chat_id):
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
                "🎛️ **Admin Feature Toggles**\n\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline(sleep_btn_text, b"toggle_admin_sleep")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )
            
        elif data == "toggle_admin_ai" and is_admin(chat_id):
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
                "🎛️ **Admin Feature Toggles**\n\nLock or unlock features for all tenants.",
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
                "🎛️ **Admin Feature Toggles**\n\nLock or unlock features for all tenants.",
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

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done patching back buttons and admin features.")