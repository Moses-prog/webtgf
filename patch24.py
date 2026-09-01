with open('forwarder.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_logic = '''    incoming_id_clean = str(event.chat_id).replace("-100", "").replace("-", "")
    for src in source_channels:
        if str(src).startswith("@") or not any(char.isdigit() for char in str(src)):
            continue
        src_clean = str(src).replace("-100", "").replace("-", "")
        if src_clean == incoming_id_clean:
            is_source = True
            break'''

new_logic = '''    incoming_id_clean = str(event.chat_id).replace("-100", "").replace("-", "")
    for src in source_channels:
        if str(src).startswith("@") or not any(char.isdigit() for char in str(src)):
            continue
        src_clean = str(src).replace("-100", "").replace("-", "")
        print(f"[DEBUG-MATCH] Comparing incoming: {incoming_id_clean} with saved: {src_clean}")
        if src_clean == incoming_id_clean:
            print(f"[DEBUG-MATCH] SUCCESS! {src_clean} == {incoming_id_clean}")
            is_source = True
            break'''

if old_logic in c:
    c = c.replace(old_logic, new_logic)
    with open('forwarder.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Debug matching injected.")
else:
    print("Could not find block.")
