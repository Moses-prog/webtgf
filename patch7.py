import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = 0
for i, line in enumerate(lines):
    if skip > 0:
        skip -= 1
        continue
    
    if 'elif data == "toggle_admin_ai"' in line:
        good_block = '''        elif data == "toggle_admin_ai" and is_admin(chat_id):
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
            )\\n'''
        new_lines.append(good_block)
        
        # skip next lines until the end of the block
        j = i + 1
        while j < len(lines):
            if 'elif data == "admin_ai_broadcast"' in lines[j]:
                break
            skip += 1
            j += 1
    else:
        new_lines.append(line)

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)