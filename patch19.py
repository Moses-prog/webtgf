with open('forwarder.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

import re

new_content = []
skip = False
for i, l in enumerate(lines):
    if l.strip() == 'success = False' and 'try:' in lines[i-1]:
        # This is where we rewrite the whole block up to the finally:
        new_block = '''        success = False
        for target in target_channels:
            try:
                t = int(target)
            except ValueError:
                t = target
                
            try:
                if media_to_send and not isinstance(media_to_send, MessageMediaWebPage):
                    await client.send_file(t, media_to_send, caption=modified_text)
                else:
                    if modified_text:
                        await client.send_message(t, modified_text, link_preview=True)
                success = True
            except Exception as e:
                print(f"[Tenant {chat_id}] Failed to forward cleanly to {t}: {e}")
                # Try fallback just for this target
                if modified_text:
                    try:
                        await client.send_message(t, modified_text)
                    except Exception as fallback_e:
                        print(f"[Tenant {chat_id}] Fallback failed for {t}: {fallback_e}")
                        
        if success:
            import datetime
            from database_manager import get_stats, save_stats
            today = str(datetime.date.today())
            stats = get_stats()
            
            if stats.get("date") != today:
                stats["today"] = 0
                stats["date"] = today
                
            stats["total"] = stats.get("total", 0) + 1
            stats["today"] = stats.get("today", 0) + 1
            
            save_stats(stats)
'''
        # We need to skip lines until 'finally:'
        skip = True
        new_content.append(new_block)
    elif skip and l.strip() == 'finally:':
        skip = False
        new_content.append(l)
    elif not skip:
        new_content.append(l)

with open('forwarder.py', 'w', encoding='utf-8') as f:
    f.write(''.join(new_content))
