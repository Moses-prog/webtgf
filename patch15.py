import codecs

with codecs.open('forwarder.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_logic = '''        if media_to_send and not isinstance(media_to_send, MessageMediaWebPage):
            for target in target_channels:
                await client.send_file(target, media_to_send, caption=modified_text)
                success = True
        else:
            if modified_text:
                for target in target_channels:
                    await client.send_message(target, modified_text, link_preview=True)
                    success = True'''

new_logic = '''        if media_to_send and not isinstance(media_to_send, MessageMediaWebPage):
            for target in target_channels:
                try: t = int(target)
                except ValueError: t = target
                await client.send_file(t, media_to_send, caption=modified_text)
                success = True
        else:
            if modified_text:
                for target in target_channels:
                    try: t = int(target)
                    except ValueError: t = target
                    await client.send_message(t, modified_text, link_preview=True)
                    success = True'''

if old_logic in c:
    c = c.replace(old_logic, new_logic)
else:
    print("WARNING: Could not find old_logic")

old_fallback = '''        if modified_text:
            for target in target_channels:
                await client.send_message(target, modified_text)'''

new_fallback = '''        if modified_text:
            for target in target_channels:
                try: t = int(target)
                except ValueError: t = target
                await client.send_message(t, modified_text)'''

if old_fallback in c:
    c = c.replace(old_fallback, new_fallback)
else:
    print("WARNING: Could not find old_fallback")

with codecs.open('forwarder.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Patch applied to forwarder.py.")