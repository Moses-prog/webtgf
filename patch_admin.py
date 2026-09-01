with open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add to Admin Menu
if 'deletion_unlocked' not in c:
    c = c.replace(
        'status_drip = "✅" if toggles.get("drip_posting_unlocked", False) else "❌"',
        'status_drip = "✅" if toggles.get("drip_posting_unlocked", False) else "❌"\n    status_del = "✅" if toggles.get("deletion_unlocked", False) else "❌"'
    )
    c = c.replace(
        '[Button.inline(f"{status_drip} Unlock Drip Posting", b"admin_toggle_drip")]',
        '[Button.inline(f"{status_drip} Unlock Drip Posting", b"admin_toggle_drip")],\n        [Button.inline(f"{status_del} Unlock Deletion Suite", b"admin_toggle_del")]'
    )
    
    admin_toggle_code = '''
        elif data == "admin_toggle_del":
            if not is_admin(chat_id): return
            toggles = get_feature_toggles()
            toggles["deletion_unlocked"] = not toggles.get("deletion_unlocked", False)
            save_feature_toggles(toggles)
            await admin_dashboard(event, chat_id)
            return'''
    c = c.replace(
        'elif data == "admin_toggle_drip":',
        admin_toggle_code.strip() + '\n\n        elif data == "admin_toggle_drip":'
    )

with open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("Admin menu updated.")
