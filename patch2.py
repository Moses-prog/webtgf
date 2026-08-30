with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

code = '''
        elif step == "waiting_for_sleep_settings":
            try:
                parts = text.split("-")
                if len(parts) != 3:
                    raise ValueError
                start_t = parts[0].strip()
                end_t = parts[1].strip()
                offset = parts[2].strip()
                
                # validate
                import re as regex
                if not regex.match(r'^\d{1,2}:\d{2}$', start_t) or not regex.match(r'^\d{1,2}:\d{2}$', end_t):
                    raise ValueError
                float(offset) # test if it's a number
                
                user_data["sleep_mode"] = user_data.get("sleep_mode", {})
                user_data["sleep_mode"]["start_time"] = start_t
                user_data["sleep_mode"]["end_time"] = end_t
                user_data["sleep_mode"]["timezone_offset"] = offset
                user_data["sleep_mode"]["enabled"] = True
                save_user_data(chat_id, user_data)
                
                user_states[chat_id] = None
                await event.respond("? **Sleep settings updated!**\\n\\nMessages will now be queued during this window.", buttons=get_main_keyboard(chat_id))
            except:
                await event.respond("? **Invalid format.**\\nPlease use the exact format:\\n22:00 - 08:00 - -5", buttons=[[Button.inline("?? Cancel", b"back")]])
            return
'''

c = re.sub(r'# --- WORD SWAPPER STEPS ---', code + '\n          # --- WORD SWAPPER STEPS ---', c)
with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
