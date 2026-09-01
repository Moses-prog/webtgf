import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update main keyboard
old_menu = '''            [Button.inline("✨ Modification Rules", b"menu_modifications")],
            [Button.inline("🚀 Auto-Posting Suite", b"menu_autoposting")],
            [Button.inline("⚙️ Settings Panel", b"menu_settings")],'''

new_menu = '''            [Button.inline("✨ Modification Rules", b"menu_modifications")],
            [Button.inline("🚀 Auto-Posting Suite", b"menu_autoposting")],
            [Button.inline("📖 How to Use the Bot", b"menu_instructions")],
            [Button.inline("⚙️ Settings Panel", b"menu_settings")],'''

if old_menu in c:
    c = c.replace(old_menu, new_menu)
else:
    print("WARNING: Could not find main menu section to replace.")

# 2. Add callback handler for menu_instructions
old_callback = '''        elif data == "menu_settings":'''

new_callback = '''        elif data == "menu_instructions":
            text = (
                "📖 **Comprehensive User Guide**\\n\\n"
                "Welcome to the ultimate auto-forwarding suite! Here's how to set up your workflow:\\n\\n"
                "**1️⃣ Connect Your Account**\\n"
                "The bot uses your Telegram account to read messages from sources and send them to targets.\\n\\n"
                "**2️⃣ Add Sources & Targets (Max 15 each)**\\n"
                "• **Sources**: Where the bot copies messages *from*.\\n"
                "• **Targets**: Where the bot pastes messages *to*.\\n"
                "*How to add/remove:* Click Sources or Targets, then simply **forward a message** from the channel to the bot! (Forwarding it again removes it). You can also manually paste private links (	.me/c/...) or @usernames.\\n\\n"
                "**3️⃣ Modification Rules (Editing)**\\n"
                "• **Word Swapper**: Automatically replace specific words (e.g., 'Join their group' -> 'Join our group').\\n"
                "• **Image Branding**: Automatically overwrite any pictures with your own promotional image.\\n"
                "• **Link Replacement**: Force all forwarded links to be replaced with your own global link.\\n\\n"
                "**4️⃣ Auto-Posting Suite**\\n"
                "• **Drip Posting**: Instead of flooding your channel with 10 forwarded messages at once, Drip Posting holds them in a queue and sends them one by one every X minutes.\\n"
                "• **Sleep Mode**: Set a blackout window (e.g., 10 PM - 8 AM). The bot will queue any incoming messages overnight and unleash them when you wake up!"
            )
            buttons = [[Button.inline("🔙 Back to Main Menu", b"back")]]
            await event.edit(text, buttons=buttons)
            return

        elif data == "menu_settings":'''

if old_callback in c:
    c = c.replace(old_callback, new_callback)
else:
    print("WARNING: Could not find menu_settings callback to replace.")

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Patch applied.")