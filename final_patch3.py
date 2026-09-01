import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update admin_features block
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

# 2. Update toggle_admin_drip to include sleep toggle in its UI refresh
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

# 3. Update toggle_admin_ai to include sleep toggle in its UI refresh
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

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done patching.")
