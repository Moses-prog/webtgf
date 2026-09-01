import re

with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update Main Menu
main_menu_pattern = r'        else:\\n\s+buttons\.extend\(\[\\n\s+\[Button\.inline.*?menu_about"\)\]\\n\s+\]\)'
main_menu_new = '''        else:
            buttons.extend([
                [Button.inline(f"📌 Sources ({len(sources)})", b"menu_sources"), Button.inline(f"🎯 Targets ({len(targets)})", b"menu_targets")],
                [Button.inline("✨ Modification Rules", b"menu_modifications")],
                [Button.inline("🚀 Auto-Posting Suite", b"menu_autoposting")],
                [Button.inline("⚙️ Settings Panel", b"menu_settings")],
                [Button.inline("🔌 Disconnect Account", b"disconnect_account")],
                [Button.inline("💬 24/7 Support", b"menu_support"), Button.inline("ℹ️ About Us", b"menu_about")]
            ])'''

c = re.sub(main_menu_pattern, main_menu_new, c, flags=re.DOTALL)


# 2. Add sub-menus, Sleep Mode callbacks, and Queue callbacks
submenus_and_sleep = '''
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

        elif data == "menu_sleep":
            toggles = get_feature_toggles()
            if not toggles.get("sleep_mode_unlocked", False) and not is_admin(chat_id):
                await event.answer("👨‍🍳 Still cooking... This feature is locked by the Admin.", alert=True)
                return
                
            user_data = get_user_data(chat_id)
            sleep_mode = user_data.get("sleep_mode", {})
            
            is_enabled = sleep_mode.get("enabled", False)
            start_t = sleep_mode.get("start_time", "22:00")
            end_t = sleep_mode.get("end_time", "08:00")
            offset = sleep_mode.get("timezone_offset", 0)
            
            status = "✅ ON" if is_enabled else "❌ OFF"
            text = (
                "💤 **Sleep Mode / Blackout Window**\\n\\n"
                "Hold all incoming messages during specific hours and drip them out in the morning.\\n\\n"
                f"**Status:** {status}\\n"
                f"**Start Time:** {start_t}\\n"
                f"**End Time:** {end_t}\\n"
                f"**Timezone Offset (UTC):** {offset}\\n\\n"
                "Use the buttons below to configure your sleep window."
            )
            buttons = [
                [Button.inline("Toggle ON/OFF", b"sleep_toggle")],
                [Button.inline("✏️ Edit Times", b"sleep_edit")],
                [Button.inline("🔙 Back", b"back_autoposting")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "sleep_toggle":
            user_data = get_user_data(chat_id)
            sleep_mode = user_data.get("sleep_mode", {})
            sleep_mode["enabled"] = not sleep_mode.get("enabled", False)
            user_data["sleep_mode"] = sleep_mode
            save_user_data(chat_id, user_data)
            await event.answer("Sleep Mode toggled!", alert=False)
            
            # Refresh menu
            is_enabled = sleep_mode.get("enabled", False)
            start_t = sleep_mode.get("start_time", "22:00")
            end_t = sleep_mode.get("end_time", "08:00")
            offset = sleep_mode.get("timezone_offset", 0)
            status = "✅ ON" if is_enabled else "❌ OFF"
            text = (
                "💤 **Sleep Mode / Blackout Window**\\n\\n"
                "Hold all incoming messages during specific hours and drip them out in the morning.\\n\\n"
                f"**Status:** {status}\\n"
                f"**Start Time:** {start_t}\\n"
                f"**End Time:** {end_t}\\n"
                f"**Timezone Offset (UTC):** {offset}\\n\\n"
                "Use the buttons below to configure your sleep window."
            )
            buttons = [
                [Button.inline("Toggle ON/OFF", b"sleep_toggle")],
                [Button.inline("✏️ Edit Times", b"sleep_edit")],
                [Button.inline("🔙 Back", b"back_autoposting")]
            ]
            await event.edit(text, buttons=buttons)
            return
            
        elif data == "sleep_edit":
            user_states[chat_id] = {"step": "waiting_for_sleep_settings"}
            await event.edit(
                "✏️ **Edit Sleep Settings**\\n\\n"
                "Please reply with your settings in this exact format:\\n"
                "[Start Time] - [End Time] - [UTC Offset]\\n\\n"
                "**Example:**\\n"
                "22:00 - 08:00 - -5\\n"
                "*(This means 10 PM to 8 AM in EST timezone)*\\n\\n"
                "**Example 2 (London/UTC):**\\n"
                "23:00 - 07:00 - 0\\n\\n"
                "Please reply with your times (24-hour format):",
                buttons=[[Button.inline("🔙 Cancel", b"back_autoposting")]]
            )
            return

        elif data == "menu_queue":
            user_data = get_user_data(chat_id)
            queue = user_data.get("drip_queue", [])
            
            if not queue:
                await event.edit("📥 **Message Queue**\\n\\nYour queue is currently empty.", buttons=[[Button.inline("🔙 Back", b"back_autoposting")]])
                return
                
            text = f"📥 **Message Queue** ({len(queue)} messages)\\n\\n"
            for i, q in enumerate(queue[:10]):
                text += f"**{i+1}.** {q.get('preview', '[Media]')}\\n"
                
            if len(queue) > 10:
                text += f"\\n*...and {len(queue)-10} more.*"
                
            buttons = [
                [Button.inline("▶️ Forward All Now", b"queue_forward_all")],
                [Button.inline("❌ Cancel All", b"queue_clear")],
                [Button.inline("🔙 Back", b"back_autoposting")]
            ]
            await event.edit(text, buttons=buttons)
            return
            
        elif data == "queue_forward_all":
            user_data = get_user_data(chat_id)
            user_data["drip_interval"] = 0
            user_data["sleep_mode"] = user_data.get("sleep_mode", {})
            user_data["sleep_mode"]["enabled"] = False
            save_user_data(chat_id, user_data)
            await event.answer("Queue flushing initiated! Sleep mode & Drip interval have been disabled to allow instant sending.", alert=True)
            await event.edit("✅ **Queue Flushed**\\n\\nAll messages will be sent momentarily.", buttons=[[Button.inline("🔙 Back", b"back_autoposting")]])
            return
            
        elif data == "queue_clear":
            user_data = get_user_data(chat_id)
            user_data["drip_queue"] = []
            save_user_data(chat_id, user_data)
            await event.answer("Queue cleared!", alert=True)
            await event.edit("🗑️ **Queue Cleared**\\n\\nAll held messages have been deleted.", buttons=[[Button.inline("🔙 Back", b"back_autoposting")]])
            return\\n'''

target_drip = '        elif data == "menu_drip_posting":'
idx_drip = c.find(target_drip)
if idx_drip != -1:
    c = c[:idx_drip] + submenus_and_sleep + c[idx_drip:]


# 3. Update Admin Features Block to include Sleep Mode
admin_features_pattern = r'        elif data == "admin_features" and is_admin\(chat_id\):.*?\(btn_text, b"toggle_admin_drip"\)\],\\n\s+\[Button\.inline\(ai_btn_text, b"toggle_admin_ai"\)\],\\n\s+\[Button\.inline\(".*? Back", b"admin_panel"\)\]\\n\s+\]\\n\s+\)'

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
                "🎛️ **Admin Feature Toggles**\\n\\nLock or unlock features for all tenants.",
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

c = re.sub(admin_features_pattern, admin_features_new, c, flags=re.DOTALL)


# 4. Replace back buttons in specific sub-menus
def replace_back_safe(code, marker, new_back):
    lines = code.split('\\n')
    in_block = False
    for i, line in enumerate(lines):
        if marker in line:
            in_block = True
        if in_block and ('b"back"' in line or "b'back'" in line) and 'Button.inline' in line:
            lines[i] = line.replace('b"back"', f'b"{new_back}"').replace("b'back'", f'b"{new_back}"')
            in_block = False
    return '\\n'.join(lines)

c = replace_back_safe(c, 'elif data == "menu_image":', 'back_modifications')
c = replace_back_safe(c, 'elif data == "menu_words":', 'back_modifications')
c = replace_back_safe(c, 'elif data == "menu_links":', 'back_modifications')
c = replace_back_safe(c, 'elif data == "menu_drip_posting":', 'back_autoposting')

with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done restoring and patching.")