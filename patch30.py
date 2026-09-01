with open('forwarder.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_logic = '''    # 2. Replace Links
    link_replacement = user_data.get("replace_all_links_with", "").strip()
    if link_replacement:
        # Match http/https, www, domain.com/path, and common domains without protocol
        url_pattern = r'(?i)(?:https?://|www\\.)[^\\s]+|\\b[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,6}/[^\\s]*|\\b(?:t\\.me|telegram\\.me|youtube\\.com|youtu\\.be|instagram\\.com|twitter\\.com|x\\.com|facebook\\.com|tiktok\\.com|bit\\.ly)[^\\s]*'
        
        def link_replacer(match):
            matched_str = match.group(0)
            # If the original link did NOT have http/https, we remove it from the replacement link too!
            if not matched_str.lower().startswith('http'):
                return re.sub(r'^https?://', '', link_replacement, flags=re.IGNORECASE)
            return link_replacement
            
        text = re.sub(url_pattern, link_replacer, text)'''

start_idx = c.find('    # 2. Replace Links')
end_idx = c.find('    # 3. Replace Usernames')
if start_idx != -1 and end_idx != -1:
    c = c[:start_idx] + new_logic + '\n\n' + c[end_idx:]
    with open('forwarder.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Replaced!")
else:
    print("Not found")
