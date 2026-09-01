import codecs

with codecs.open('control_bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_block = '''        elif data == "menu_instructions":
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
            return'''

new_block = '''        elif data == "menu_instructions":
            text = (
                "📖 **How To Use This Bot (Step-by-Step Guide)**\\n\\n"
                "Welcome! Listen carefully, let's break down how this bot works so you can start forwarding your messages sharp sharp without any stress.\\n\\n"
                "Select a topic below to read the step-by-step guide for it:"
            )
            buttons = [
                [Button.inline("📲 1. How to Connect Account", b"inst_connect")],
                [Button.inline("🎯 2. Sources & Targets", b"inst_channels")],
                [Button.inline("✨ 3. Modifying Messages", b"inst_modify")],
                [Button.inline("🚀 4. Auto-Posting (Drip/Sleep)", b"inst_auto")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "inst_connect":
            text = (
                "📲 **Step 1: Connecting Your Account**\\n\\n"
                "First things first, the bot needs to use your Telegram account to read messages and forward them for you.\\n\\n"
                "**How to do it:**\\n"
                "1. On the Main Menu, click on **Connect Account**.\\n"
                "2. Enter your phone number (including country code, e.g., +234...).\\n"
                "3. Telegram will send a login code to your Telegram app.\\n"
                "4. Type the code here in the bot. (If you have a 2-Step Verification password, the bot will ask for it).\\n\\n"
                "Once connected, your status will change to ✅ Connected. Now you are ready for action!"
            )
            buttons = [[Button.inline("🔙 Back to Instructions", b"menu_instructions")]]
            await event.edit(text, buttons=buttons)
            return

        elif data == "inst_channels":
            text = (
                "🎯 **Step 2: Adding Sources and Targets**\\n\\n"
                "This is where you tell the bot where to copy messages *from* (Source) and where to paste them *to* (Target).\\n\\n"
                "**How to add them:**\\n"
                "1. Click **Sources** or **Targets** on the main menu.\\n"
                "2. Go to the channel you want to add, and **forward any message** from it to this bot.\\n"
                "3. **What if forwarding is blocked?** No shaking! Just copy any post link from the channel (like https://t.me/c/12345/67) and paste it to the bot. It will extract the ID automatically!\\n"
                "4. You can also just type the @username of the channel.\\n\\n"
                "**To Remove a channel:** Just forward a message from it again, and the bot will remove it from your list. Sharp sharp!"
            )
            buttons = [[Button.inline("🔙 Back to Instructions", b"menu_instructions")]]
            await event.edit(text, buttons=buttons)
            return

        elif data == "inst_modify":
            text = (
                "✨ **Step 3: Modifying Your Messages**\\n\\n"
                "You don't want to just forward messages raw. You want to brand them as your own! Click **Modification Rules** on the main menu to set this up.\\n\\n"
                "• **✏️ Word Swapper**: Did the source channel type their name? Tell the bot to swap their name to your own name automatically!\\n"
                "• **🖼 Image Branding**: You can set a custom photo. If the source posts a picture, the bot will remove their picture and attach your own promotional picture instead.\\n"
                "• **🔗 Link Replacement**: The bot can scan for any link in the message and replace it with your own referral link or group link."
            )
            buttons = [[Button.inline("🔙 Back to Instructions", b"menu_instructions")]]
            await event.edit(text, buttons=buttons)
            return

        elif data == "inst_auto":
            text = (
                "🚀 **Step 4: Auto-Posting Suite**\\n\\n"
                "Don't just dump 20 messages into your channel at once, it will annoy your subscribers. Manage the flow!\\n\\n"
                "• **🕐 Drip Posting**: This holds your forwarded messages in a queue, and releases them one by one based on the time interval you set (e.g., every 5 minutes). Keeps your channel active all day!\\n"
                "• **💤 Sleep Mode**: Set your sleeping time (e.g., 10:00 PM to 7:00 AM). The bot will hold all messages that arrive in the night. Once you wake up by 7:00 AM, it will start dripping them automatically.\\n\\n"
                "You can always check your held messages in the **📥 View Queue** menu."
            )
            buttons = [[Button.inline("🔙 Back to Instructions", b"menu_instructions")]]
            await event.edit(text, buttons=buttons)
            return'''

if old_block in c:
    c = c.replace(old_block, new_block)
else:
    print("WARNING: Could not find old_block")

with codecs.open('control_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Patch applied.")