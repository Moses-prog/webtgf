import codecs

with codecs.open('forwarder.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_logic = '''    is_source = False
    if str(event.chat_id) in source_channels:
        is_source = True
    elif hasattr(event, 'chat') and event.chat and hasattr(event.chat, 'username') and event.chat.username:
        if f"@{event.chat.username}" in source_channels or event.chat.username in source_channels:
            is_source = True'''

new_logic = '''    is_source = False
    
    # Robust numeric ID matching
    incoming_id_clean = str(event.chat_id).replace("-100", "").replace("-", "")
    for src in source_channels:
        if str(src).startswith("@") or not any(char.isdigit() for char in str(src)):
            continue
        src_clean = str(src).replace("-100", "").replace("-", "")
        if src_clean == incoming_id_clean:
            is_source = True
            break
            
    # Exact string match fallback
    if not is_source and str(event.chat_id) in source_channels:
        is_source = True
        
    # Username matching
    if not is_source and hasattr(event, 'chat') and event.chat and hasattr(event.chat, 'username') and event.chat.username:
        if f"@{event.chat.username}" in source_channels or event.chat.username in source_channels:
            is_source = True'''

if old_logic in c:
    c = c.replace(old_logic, new_logic)
    with codecs.open('forwarder.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Patch applied.")
else:
    print("WARNING: Could not find old_logic")
