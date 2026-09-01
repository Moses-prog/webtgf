import re

with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

good_code = '''
        elif data == b"menu_sleep":
            user_data = get_user_data(chat_id)
            sleep_mode = user_data.get("sleep_mode", {})
            
            is_enabled = sleep_mode.get("enabled", False)
            start_t = sleep_mode.get("start_time", "22:00")
            end_t = sleep_mode.get("end_time", "08:00")
            offset = sleep_mode.get("timezone_offset", 0)
            
            status = "? ON" if is_enabled else "? OFF"
            text = (
                "?? **Sleep Mode / Blackout Window**\\n\\n"
                "Hold all incoming messages during specific hours and drip them out in the morning.\\n\\n"
                f"**Status:** {status}\\n"
                f"**Start Time:** {start_t}\\n"
                f"**End Time:** {end_t}\\n"
                f"**Timezone Offset (UTC):** {offset}\\n\\n"
                "Use the buttons below to configure your sleep window."
            )
            
            buttons = [
                [Button.inline("Toggle ON/OFF", b"sleep_toggle")],
                [Button.inline("?? Edit Times", b"sleep_edit")],
                [Button.inline("?? Back", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == b"sleep_toggle":
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
            status = "? ON" if is_enabled else "? OFF"
            text = (
                "?? **Sleep Mode / Blackout Window**\\n\\n"
                "Hold all incoming messages during specific hours and drip them out in the morning.\\n\\n"
                f"**Status:** {status}\\n"
                f"**Start Time:** {start_t}\\n"
                f"**End Time:** {end_t}\\n"
                f"**Timezone Offset (UTC):** {offset}\\n\\n"
                "Use the buttons below to configure your sleep window."
            )
            buttons = [
                [Button.inline("Toggle ON/OFF", b"sleep_toggle")],
                [Button.inline("?? Edit Times", b"sleep_edit")],
                [Button.inline("?? Back", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return
            
        elif data == b"sleep_edit":
            user_states[chat_id] = {"step": "waiting_for_sleep_settings"}
            await event.edit(
                "?? **Edit Sleep Settings**\\n\\n"
                "Please reply with your settings in this exact format:\\n"
                "[Start Time] - [End Time] - [UTC Offset]\\n\\n"
                "**Example:**\\n"
                "22:00 - 08:00 - -5\\n"
                "*(This means 10 PM to 8 AM in EST timezone)*\\n\\n"
                "**Example 2 (London/UTC):**\\n"
                "23:00 - 07:00 - 0\\n\\n"
                "Please reply with your times (24-hour format):",
                buttons=[[Button.inline("?? Cancel", b"back")]]
            )
            return

        elif data == b"menu_queue":
            user_data = get_user_data(chat_id)
            queue = user_data.get("drip_queue", [])
            
            if not queue:
                await event.edit("?? **Message Queue**\\n\\nYour queue is currently empty.", buttons=[[Button.inline("?? Back", b"back")]])
                return
                
            text = f"?? **Message Queue** ({len(queue)} messages)\\n\\n"
            for i, q in enumerate(queue[:10]):
                text += f"**{i+1}.** {q.get('preview', '[Media]')}\\n"
                
            if len(queue) > 10:
                text += f"\\n*...and {len(queue)-10} more.*"
                
            buttons = [
                [Button.inline("?? Forward All Now", b"queue_forward_all")],
                [Button.inline("? Cancel All", b"queue_clear")],
                [Button.inline("?? Back", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return
            
        elif data == b"queue_forward_all":
            user_data = get_user_data(chat_id)
            user_data["drip_interval"] = 0
            user_data["sleep_mode"] = user_data.get("sleep_mode", {})
            user_data["sleep_mode"]["enabled"] = False
            save_user_data(chat_id, user_data)
            await event.answer("Queue flushing initiated! Sleep mode & Drip interval have been disabled to allow instant sending.", alert=True)
            await event.edit("? **Queue Flushed**\\n\\nAll messages will be sent momentarily.", buttons=[[Button.inline("?? Back", b"back")]])
            return
            
        elif data == b"queue_clear":
            user_data = get_user_data(chat_id)
            user_data["drip_queue"] = []
            save_user_data(chat_id, user_data)
            await event.answer("Queue cleared!", alert=True)
            await event.edit("??? **Queue Cleared**\\n\\nAll held messages have been deleted.", buttons=[[Button.inline("?? Back", b"back")]])
            return
'''

c = re.sub(r'        elif data == b"menu_sleep":.*?return\n', good_code, c, flags=re.DOTALL)
with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
