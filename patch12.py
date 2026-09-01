import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_logic = '''        if state == "waiting_for_sources":
            current_list = user_data.get("sources", [])
            for item in new_items:
                if item not in current_list:
                    if len(current_list) >= 15:
                        await event.respond("⚠️ You can only have a maximum of 15 sources. Some items were not added.")
                        break
                    current_list.append(item)
            user_data["sources"] = current_list
        else:
            current_list = user_data.get("targets", [])
            for item in new_items:
                if item not in current_list:
                    if len(current_list) >= 15:
                        await event.respond("⚠️ You can only have a maximum of 15 targets. Some items were not added.")
                        break
                    current_list.append(item)
            user_data["targets"] = current_list
            
        save_user_data(chat_id, user_data)
        user_states[chat_id] = None
        await event.respond(f"✅ Added: {', '.join(new_items)}", buttons=get_main_keyboard(chat_id))'''

new_logic = '''        added = []
        removed = []
        
        if state == "waiting_for_sources":
            current_list = user_data.get("sources", [])
            for item in new_items:
                if item in current_list:
                    current_list.remove(item)
                    removed.append(item)
                else:
                    if len(current_list) >= 15:
                        await event.respond("⚠️ You can only have a maximum of 15 sources. Some items were not added.")
                        break
                    current_list.append(item)
                    added.append(item)
            user_data["sources"] = current_list
        else:
            current_list = user_data.get("targets", [])
            for item in new_items:
                if item in current_list:
                    current_list.remove(item)
                    removed.append(item)
                else:
                    if len(current_list) >= 15:
                        await event.respond("⚠️ You can only have a maximum of 15 targets. Some items were not added.")
                        break
                    current_list.append(item)
                    added.append(item)
            user_data["targets"] = current_list
            
        save_user_data(chat_id, user_data)
        user_states[chat_id] = None
        
        res_msg = ""
        if added:
            res_msg += f"✅ Added: {', '.join(added)}\\n"
        if removed:
            res_msg += f"🗑️ Removed: {', '.join(removed)}\\n"
            
        await event.respond(res_msg.strip() or "No changes made.", buttons=get_main_keyboard(chat_id))'''

if old_logic in c:
    c = c.replace(old_logic, new_logic)
else:
    print("WARNING: Could not find old_logic")

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done patching.")