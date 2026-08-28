import os
import json
import time
import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import MessageNotModifiedError, SessionPasswordNeededError
from dotenv import load_dotenv, set_key

from database_manager import get_user_data, save_user_data, get_all_users, get_tenants, save_tenants

ENV_FILE = '.env'
TENANTS_FILE = 'tenants.json'

load_dotenv(ENV_FILE, override=True)
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

bot = TelegramClient('control_bot_session', API_ID, API_HASH)

user_states = {}
login_sessions = {}  # Temporary storage for OTP login clients



def is_admin(chat_id):
    load_dotenv(ENV_FILE, override=True)
    admin_id = os.getenv('ADMIN_ID', '').strip()
    return str(chat_id) == admin_id

def is_tenant(chat_id):
    if is_admin(chat_id):
        return True
    return str(chat_id) in get_tenants()

def get_main_keyboard(chat_id):
    user_data = get_user_data(chat_id)
    sources = user_data.get('sources', [])
    targets = user_data.get('targets', [])
    
    # Check if they have an active session string configured
    has_session = bool(user_data.get('session_string', ''))
    status_text = "🟢 Connected" if has_session else "🔴 Disconnected"
    
    buttons = [
        [Button.inline(f"📱 Account: {status_text}", b"status")],
    ]
    
    if not has_session:
        buttons.append([Button.inline("🔑 Connect Account", b"connect_account")])
        buttons.append([Button.inline("💬 24/7 Support", b"menu_support"), Button.inline("ℹ️ About Us", b"menu_about")])
    else:
        buttons.extend([
            [Button.inline(f"📌 Sources ({len(sources)})", b"menu_sources"), Button.inline(f"🎯 Targets ({len(targets)})", b"menu_targets")],
            [Button.inline("🖼 Image Branding", b"menu_image"), Button.inline("✏️ Word Swapper", b"menu_words")],
            [Button.inline("🔗 Link & Branding", b"menu_links"), Button.inline("⚙️ Settings Panel", b"menu_settings")],
            [Button.inline("🔌 Disconnect Account", b"disconnect_account")],
            [Button.inline("💬 24/7 Support", b"menu_support"), Button.inline("ℹ️ About Us", b"menu_about")]
        ])
    
    if is_admin(chat_id):
        buttons.append([Button.inline("👑 Admin Panel", b"admin_panel")])
        
    return buttons

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    chat_id = event.chat_id
    
    if not is_tenant(chat_id):
        welcome_msg = (
            "👋 **Welcome to Webtgf Manager!**\n\n"
            "You currently do not have an active subscription or your ID has not been registered.\n\n"
            f"Your Chat ID is: `{chat_id}`\n\n"
            "Please contact the administrator **@apklord55** to get access or activate your account."
        )
        await event.respond(welcome_msg)
        return
        
    user_states[chat_id] = None
    
    user_data = get_user_data(chat_id)
    if not user_data.get('session_string'):
        msg = "👋 Welcome to the **Webtgf Dashboard**!\n\nYour forwarding engine is currently **Disconnected**. Please click **🔑 Connect Account** below to securely link your Telegram account and start forwarding messages."
    else:
        msg = "👋 Welcome to the **Webtgf Dashboard**!\n\nManage your forwarding rules, channels, and replacements directly from this menu."
        
    await event.respond(msg, buttons=get_main_keyboard(chat_id))

@bot.on(events.CallbackQuery)
async def callback(event):
    chat_id = event.chat_id
    
    if not is_tenant(chat_id):
        await event.answer("Unauthorized. Contact @apklord55", alert=True)
        return
        
    data = event.data.decode('utf-8')
    
    try:
        if data == "status":
            await event.answer("Refreshing status...")
            await event.edit(buttons=get_main_keyboard(chat_id))
            return
            
        elif data == "menu_about":
            user_states[chat_id] = None
            about_text = (
                "ℹ️ **About Webtgf Manager**\n\n"
                "**Version:** 2.0.0 (Multi-Tenant Pro)\n"
                "**Developed by:** @apklord55\n\n"
                "This engine was custom-built to provide the fastest, most reliable, and secure automated forwarding experience on Telegram. "
                "For inquiries, custom bot development, or technical support, please contact the developer."
            )
            await event.edit(about_text, buttons=[[Button.inline("🔙 Back", b"back")]])
            return
            
        elif data == "menu_support":
            user_states[chat_id] = None
            support_text = (
                "💬 **24/7 Technical Support**\n\n"
                "If you are experiencing issues or need help configuring your targets and sources, please contact the developer directly:\n\n"
                "👉 **Contact:** @apklord55"
            )
            await event.edit(support_text, buttons=[[Button.inline("🔙 Back", b"back")]])
            return
            
        elif data == "back":
            user_states[chat_id] = None
            await event.edit("👋 Welcome to the **Webtgf Dashboard**!", buttons=get_main_keyboard(chat_id))
            return

        # -----------------------------------------------------
        # SETTINGS PANEL
        # -----------------------------------------------------
        elif data == "menu_settings":
            user_data = get_user_data(chat_id)
            delay_enabled = user_data.get("smart_delay_enabled", False)
            status = "✅ ON" if delay_enabled else "❌ OFF"
            
            text = (
                "⚙️ **Advanced Settings Panel**\n\n"
                "**1. Smart Delay (Anti-Ban)**\n"
                "If enabled, the bot will wait 1 to 3 minutes before forwarding, making it look like a real human reading and typing.\n"
                f"Current Status: {status}"
            )
            
            buttons = [
                [Button.inline(f"Toggle Smart Delay: {status}", b"toggle_smart_delay")],
                [Button.inline("🔙 Back", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return
            
        elif data == "toggle_smart_delay":
            user_data = get_user_data(chat_id)
            user_data["smart_delay_enabled"] = not user_data.get("smart_delay_enabled", False)
            save_user_data(chat_id, user_data)
            
            delay_enabled = user_data.get("smart_delay_enabled", False)
            status = "✅ ON" if delay_enabled else "❌ OFF"
            await event.answer(f"Smart Delay turned {status}!", alert=True)
            
            # Refresh menu
            text = (
                "⚙️ **Advanced Settings Panel**\n\n"
                "**1. Smart Delay (Anti-Ban)**\n"
                "If enabled, the bot will wait 1 to 3 minutes before forwarding, making it look like a real human reading and typing.\n"
                f"Current Status: {status}"
            )
            buttons = [
                [Button.inline(f"Toggle Smart Delay: {status}", b"toggle_smart_delay")],
                [Button.inline("🔙 Back", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return

        # -----------------------------------------------------
        # CONNECT / DISCONNECT ACCOUNT LOGIC
        # -----------------------------------------------------
        elif data == "connect_account":
            user_states[chat_id] = {"step": "waiting_for_api_id"}
            await event.edit(
                "🔑 **Connect Your Telegram Account**\n\n"
                "To forward messages, we need to securely connect your account. First, we need your `API_ID`.\n\n"
                "Please reply with your `API_ID` (numbers only).\n*(You can get this from my.telegram.org)*",
                buttons=[[Button.inline("🔙 Cancel", b"back")]]
            )
            return
            
        elif data == "disconnect_account":
            user_data = get_user_data(chat_id)
            user_data["session_string"] = ""
            user_data["api_id"] = ""
            user_data["api_hash"] = ""
            save_user_data(chat_id, user_data)
            await event.edit("🔌 **Account Disconnected!**\n\nYour forwarding engine has been stopped.", buttons=get_main_keyboard(chat_id))
            return

        # -----------------------------------------------------
        # CONFIGURATION MENUS
        # -----------------------------------------------------
        user_data = get_user_data(chat_id)
        if not user_data.get('session_string') and data.startswith("menu_"):
            await event.answer("⚠️ You must connect your account first!", alert=True)
            return

        if data == "menu_sources":
            user_states[chat_id] = "waiting_for_sources"
            current = ", ".join(user_data.get('sources', []))
            await event.edit(
                f"**📌 Edit Sources**\n\nCurrent Sources:\n`{current}`\n\n"
                "👉 **How to add a source:**\n"
                "Simply **Forward any message** from the channel to me here!\n"
                "*(Or manually reply with a `@username` or `-100` ID)*\n\n"
                "Send /cancel to go back.",
                buttons=[[Button.inline("🔙 Back", b"back")]]
            )
            
        elif data == "menu_targets":
            user_states[chat_id] = "waiting_for_targets"
            current = ", ".join(user_data.get('targets', []))
            await event.edit(
                f"**🎯 Edit Targets**\n\nCurrent Targets:\n`{current}`\n\n"
                "👉 **How to add a target:**\n"
                "Simply **Forward any message** from the channel to me here!\n"
                "*(Or manually reply with a comma-separated list of `@username`)*\n\n"
                "Send /cancel to go back.",
                buttons=[[Button.inline("🔙 Back", b"back")]]
            )
            
        elif data == "menu_words":
            swaps = user_data.get("text_swaps", {})
            msg = "**✏️ Word Swapper**\n\nCurrent Swaps:\n"
            if not swaps:
                msg += "*(No words are currently being swapped)*\n"
            for old, new in swaps.items():
                msg += f"• `{old}` ➡️ `{new}`\n"
            user_states[chat_id] = {"step": "waiting_for_old_word"}
            msg += "\n**What word or phrase do you want to FIND in the incoming messages?**"
            await event.edit(msg, buttons=[[Button.inline("🔙 Back", b"back")]])
    
        elif data == "menu_links":
            user_states[chat_id] = "waiting_for_link"
            current_link = user_data.get("replace_all_links_with", "")
            current_user = user_data.get("replace_all_usernames_with", "")
            await event.edit(
                f"**🔗 Link & Branding**\n\nGlobal Link: `{current_link}`\nGlobal Username: `{current_user}`\n\nReply with `LINK=https://yourlink.com` or `USER=@youruser` to update them.",
                buttons=[[Button.inline("🔙 Back", b"back")]]
            )
            
        elif data == "menu_image":
            user_states[chat_id] = "waiting_for_image"
            current_url = user_data.get("image_swap_url", "")
            current_path = user_data.get("image_swap_path", "")
            is_enabled = user_data.get("image_override_enabled", True)
            
            status = "None"
            if current_path:
                status = "Custom Photo Uploaded"
            elif current_url:
                status = current_url
                
            toggle_btn = "🔴 Turn OFF" if is_enabled else "🟢 Turn ON"
            
            await event.edit(
                f"**🖼 Image Branding**\n\nCurrent Image: `{status}`\nStatus: {'**ENABLED**' if is_enabled else '**DISABLED**'}\n\n"
                "👉 **How to set a global image:**\n"
                "Simply **Send a Photo** to the bot right now!\n"
                "*(Or manually reply with a direct image URL, or type `CLEAR` to remove it)*",
                buttons=[
                    [Button.inline(toggle_btn, b"toggle_image")],
                    [Button.inline("🔙 Back", b"back")]
                ]
            )
            
        elif data == "toggle_image":
            is_enabled = user_data.get("image_override_enabled", True)
            user_data["image_override_enabled"] = not is_enabled
            save_user_data(chat_id, user_data)
            
            current_url = user_data.get("image_swap_url", "")
            current_path = user_data.get("image_swap_path", "")
            new_status = not is_enabled
            
            status = "None"
            if current_path:
                status = "Custom Photo Uploaded"
            elif current_url:
                status = current_url
                
            toggle_btn = "🔴 Turn OFF" if new_status else "🟢 Turn ON"
            
            await event.edit(
                f"**🖼 Image Branding**\n\nCurrent Image: `{status}`\nStatus: {'**ENABLED**' if new_status else '**DISABLED**'}\n\n"
                "👉 **How to set a global image:**\n"
                "Simply **Send a Photo** to the bot right now!\n"
                "*(Or manually reply with a direct image URL, or type `CLEAR` to remove it)*",
                buttons=[
                    [Button.inline(toggle_btn, b"toggle_image")],
                    [Button.inline("🔙 Back", b"back")]
                ]
            )
            
        # -----------------------------------------------------
        # ADMIN PANEL
        # -----------------------------------------------------
        elif data == "admin_panel" and is_admin(chat_id):
            user_states[chat_id] = None
            tenants = get_tenants()
            msg = f"👑 **Admin Panel**\n\nTotal Tenants: {len(tenants)}\n\nSelect an action:"
            buttons = [
                [Button.inline("➕ Add Tenant", b"admin_add"), Button.inline("➖ Remove Tenant", b"admin_remove")],
                [Button.inline("👥 View Tenants", b"admin_view"), Button.inline("📊 Analytics", b"admin_analytics")],
                [Button.inline("📢 Broadcast", b"admin_broadcast"), Button.inline("✨ AI Generate", b"admin_ai_broadcast")],
                [Button.inline("🔙 Back to Dashboard", b"back")]
            ]
            await event.edit(msg, buttons=buttons)
            
        elif data == "admin_analytics" and is_admin(chat_id):
            import datetime
            stats_file = 'database/stats.json'
            stats = {"total": 0, "today": 0, "date": str(datetime.date.today())}
            
            if os.path.exists(stats_file):
                try:
                    with open(stats_file, 'r') as f:
                        stats = json.load(f)
                except:
                    pass
                    
            if stats.get("date") != str(datetime.date.today()):
                stats["today"] = 0
                
            tenants = get_tenants()
            
            msg = (
                "📊 **Webtgf Analytics Dashboard**\n\n"
                f"👥 **Total Tenants:** `{len(tenants)}`\n"
                f"📈 **Total Messages Forwarded:** `{stats['total']}`\n"
                f"🔥 **Messages Forwarded Today:** `{stats['today']}`\n"
            )
            await event.edit(msg, buttons=[[Button.inline("🔙 Back", b"admin_panel")]])
            
        elif data == "admin_ai_broadcast" and is_admin(chat_id):
            if not os.getenv('GEMINI_API_KEY'):
                await event.answer("⚠️ API Key not found in .env!", alert=True)
                return
            user_states[chat_id] = "waiting_for_ai_prompt"
            await event.edit(
                "✨ **AI Broadcast Generator**\n\n"
                "What feature or update do you want to announce?\n"
                "*(e.g., 'tell them we now support custom image branding')*\n\n"
                "Send /cancel to abort.",
                buttons=[[Button.inline("🔙 Cancel", b"admin_panel")]]
            )
            
        elif data == "admin_broadcast" and is_admin(chat_id):
            user_states[chat_id] = "waiting_for_broadcast"
            await event.edit(
                "📢 **Broadcast Message**\n\n"
                "Send the message (text, photo, or document) you want to broadcast to all your tenants.\n\n"
                "*(Send /cancel to abort)*", 
                buttons=[[Button.inline("🔙 Cancel", b"admin_panel")]]
            )
            
        elif data == "admin_view" and is_admin(chat_id):
            tenants = get_tenants()
            msg = "👥 **Current Tenants:**\n\n"
            if not tenants:
                msg += "No tenants added yet."
            else:
                for t in tenants:
                    msg += f"• `{t}`\n"
            await event.edit(msg, buttons=[[Button.inline("🔙 Back to Admin Panel", b"admin_panel")]])
            
        elif data == "admin_add" and is_admin(chat_id):
            user_states[chat_id] = "waiting_for_add_tenant"
            await event.edit("➕ **Add Tenant**\n\nPlease reply with the Telegram Chat ID of the user you want to grant access to.", buttons=[[Button.inline("🔙 Cancel", b"admin_panel")]])
            
        elif data == "admin_remove" and is_admin(chat_id):
            user_states[chat_id] = "waiting_for_remove_tenant"
            await event.edit("➖ **Remove Tenant**\n\nPlease reply with the Telegram Chat ID of the user you want to revoke access from.", buttons=[[Button.inline("🔙 Cancel", b"admin_panel")]])

        elif data == "ai_approve" and is_admin(chat_id):
            state = user_states.get(chat_id)
            if not isinstance(state, dict) or state.get("step") != "waiting_for_ai_approval":
                await event.answer("Session expired.", alert=True)
                return
                
            generated_message = state.get("message")
            tenants = get_tenants()
            sent_count = 0
            
            await event.edit(f"⏳ Broadcasting AI message to {len(tenants)} tenants...")
            
            for tenant_id in tenants:
                try:
                    await bot.send_message(int(tenant_id), generated_message)
                    sent_count += 1
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
                    
            user_states[chat_id] = None
            await event.edit(f"✅ **Broadcast Complete!**\n\nAI message successfully delivered to {sent_count}/{len(tenants)} tenants.", buttons=[[Button.inline("🔙 Admin Panel", b"admin_panel")]])

        else:
            await event.answer("Coming soon!", alert=True)
            
    except MessageNotModifiedError:
        pass

@bot.on(events.NewMessage)
async def text_handler(event):
    if event.text.startswith('/'):
        return
        
    chat_id = event.chat_id
    if not is_tenant(chat_id):
        return
        
    state = user_states.get(chat_id)
    if not state:
        return
        
    text = event.text.replace('`', '').strip()
    user_data = get_user_data(chat_id)

    # -----------------------------------------------------
    # OTP LOGIN FLOW (Multi-step dict state)
    # -----------------------------------------------------
    if isinstance(state, dict):
        step = state.get("step")
        
        # --- LOGIN STEPS ---
        if step == "waiting_for_api_id":
            if not text.isdigit():
                await event.respond("❌ `API_ID` must be numbers only. Try again.")
                return
            state["api_id"] = int(text)
            state["step"] = "waiting_for_api_hash"
            await event.respond("Great. Now reply with your `API_HASH` (the long random string).", buttons=[[Button.inline("🔙 Cancel", b"back")]])
            return
            
        elif step == "waiting_for_api_hash":
            state["api_hash"] = text
            state["step"] = "waiting_for_phone"
            await event.respond("Perfect. Now reply with your **Phone Number** (including the country code, e.g., `+1234567890`).", buttons=[[Button.inline("🔙 Cancel", b"back")]])
            return
            
        elif step == "waiting_for_phone":
            state["phone"] = text
            
            # Spin up a temporary client to request the code
            await event.respond("⏳ Requesting Telegram code, please wait...")
            tmp_client = TelegramClient(StringSession(), state["api_id"], state["api_hash"])
            await tmp_client.connect()
            
            try:
                res = await tmp_client.send_code_request(state["phone"])
                login_sessions[chat_id] = {
                    "client": tmp_client,
                    "phone": state["phone"],
                    "phone_code_hash": res.phone_code_hash,
                    "api_id": state["api_id"],
                    "api_hash": state["api_hash"]
                }
                state["step"] = "waiting_for_code"
                await event.respond(
                    "📩 **Telegram has sent you a login code!**\n\n"
                    "⚠️ **CRITICAL INSTRUCTION:** Telegram's security system will instantly block the login if you just send the code normally.\n\n"
                    "👉 **You MUST put spaces between the numbers.**\n"
                    "For example, if your code is `12345`, you must reply with:\n`1 2 3 4 5`\n\n"
                    "*(The bot will automatically remove the spaces for you)*", 
                    buttons=[[Button.inline("🔙 Cancel", b"back")]]
                )
            except Exception as e:
                await event.respond(f"❌ Failed to request code: {e}")
                await tmp_client.disconnect()
                user_states[chat_id] = None
            return
            
        elif step == "waiting_for_code":
            session_data = login_sessions.get(chat_id)
            if not session_data:
                await event.respond("❌ Session expired. Please try connecting again.")
                user_states[chat_id] = None
                return
                
            code = text.replace(" ", "")
            tmp_client = session_data["client"]
            
            try:
                await tmp_client.sign_in(phone=session_data["phone"], code=code, phone_code_hash=session_data["phone_code_hash"])
                
                # Success! Extract the string session
                session_string = tmp_client.session.save()
                await tmp_client.disconnect()
                del login_sessions[chat_id]
                
                # Save to user database
                user_data["api_id"] = session_data["api_id"]
                user_data["api_hash"] = session_data["api_hash"]
                user_data["session_string"] = session_string
                save_user_data(chat_id, user_data)
                
                user_states[chat_id] = None
                await event.respond("✅ **Account Successfully Connected!**\n\nYour forwarding engine will boot up momentarily.", buttons=get_main_keyboard(chat_id))
            
            except SessionPasswordNeededError:
                state["step"] = "waiting_for_password"
                await event.respond("🔒 Your account has Two-Step Verification (2FA) enabled.\n\nPlease reply with your password:", buttons=[[Button.inline("🔙 Cancel", b"back")]])
                
            except Exception as e:
                await event.respond(f"❌ Failed to login: {e}")
                await tmp_client.disconnect()
                del login_sessions[chat_id]
                user_states[chat_id] = None
            return
            
        elif step == "waiting_for_password":
            session_data = login_sessions.get(chat_id)
            if not session_data:
                return
            tmp_client = session_data["client"]
            password = text
            try:
                await tmp_client.sign_in(password=password)
                session_string = tmp_client.session.save()
                await tmp_client.disconnect()
                del login_sessions[chat_id]
                
                user_data["api_id"] = session_data["api_id"]
                user_data["api_hash"] = session_data["api_hash"]
                user_data["session_string"] = session_string
                save_user_data(chat_id, user_data)
                
                user_states[chat_id] = None
                await event.respond("✅ **Account Successfully Connected!**\n\nYour forwarding engine will boot up momentarily.", buttons=get_main_keyboard(chat_id))
            except Exception as e:
                await event.respond(f"❌ Invalid Password: {e}")
            return

        # --- WORD SWAPPER STEPS ---
        elif step == "waiting_for_old_word":
            state["old_word"] = text
            state["step"] = "waiting_for_new_word"
            await event.respond(f"Okay! Whenever I see `{state['old_word']}`, what should I replace it with?\n\n*(Type the new word, or type `DELETE` to remove this rule)*", buttons=[[Button.inline("🔙 Cancel", b"back")]])
            return
            
        elif step == "waiting_for_new_word":
            old_w = state.get("old_word")
            new_w = text
            
            if "text_swaps" not in user_data:
                user_data["text_swaps"] = {}
                
            if new_w.upper() == "DELETE":
                if old_w in user_data["text_swaps"]:
                    del user_data["text_swaps"][old_w]
                    await event.respond(f"✅ Deleted swap rule for `{old_w}`", buttons=get_main_keyboard(chat_id))
                else:
                    await event.respond(f"❌ Could not find a rule for `{old_w}` to delete.", buttons=get_main_keyboard(chat_id))
            else:
                user_data["text_swaps"][old_w] = new_w
                await event.respond(f"✅ Success! I will now replace `{old_w}` ➡️ `{new_w}`", buttons=get_main_keyboard(chat_id))
            
            save_user_data(chat_id, user_data)
            user_states[chat_id] = None
            return

    # -----------------------------------------------------
    # STRING BASED STATES (Configs)
    # -----------------------------------------------------
    if state == "waiting_for_sources" or state == "waiting_for_targets":
        if text.upper() == "CLEAR":
            if state == "waiting_for_sources":
                user_data["sources"] = []
            else:
                user_data["targets"] = []
            save_user_data(chat_id, user_data)
            user_states[chat_id] = None
            await event.respond("✅ Cleared successfully!", buttons=get_main_keyboard(chat_id))
            return
            
        from telethon.tl.types import PeerChannel, PeerChat, PeerUser
        new_items = []
        if event.fwd_from and event.fwd_from.from_id:
            peer = event.fwd_from.from_id
            if isinstance(peer, PeerChannel):
                new_items.append(f"-100{peer.channel_id}")
            elif isinstance(peer, PeerChat):
                new_items.append(f"-{peer.chat_id}")
            elif isinstance(peer, PeerUser):
                new_items.append(str(peer.user_id))
        elif text:
            new_items = [x.strip() for x in text.split(',') if x.strip()]
            
        if not new_items:
            await event.respond("❌ I couldn't detect a valid ID. Please forward a message from the channel, or type the ID manually.")
            return
            
        if state == "waiting_for_sources":
            current_list = user_data.get("sources", [])
            for item in new_items:
                if item not in current_list:
                    current_list.append(item)
            user_data["sources"] = current_list
        else:
            current_list = user_data.get("targets", [])
            for item in new_items:
                if item not in current_list:
                    current_list.append(item)
            user_data["targets"] = current_list
            
        save_user_data(chat_id, user_data)
        user_states[chat_id] = None
        await event.respond(f"✅ Added: {', '.join(new_items)}", buttons=get_main_keyboard(chat_id))
        
    elif state == "waiting_for_link":
        if text.startswith("LINK="):
            user_data["replace_all_links_with"] = text.split("=", 1)[1].strip()
            save_user_data(chat_id, user_data)
            user_states[chat_id] = None
            await event.respond("✅ Global link updated!", buttons=get_main_keyboard(chat_id))
        elif text.startswith("USER="):
            user_data["replace_all_usernames_with"] = text.split("=", 1)[1].strip()
            save_user_data(chat_id, user_data)
            user_states[chat_id] = None
            await event.respond("✅ Global username updated!", buttons=get_main_keyboard(chat_id))
        else:
            await event.respond("❌ Invalid format. Use `LINK=...` or `USER=...`")
            
    elif state == "waiting_for_image":
        if text.upper() == "CLEAR":
            user_data["image_swap_url"] = ""
            user_data["image_swap_path"] = ""
            await event.respond("✅ Image override cleared!", buttons=get_main_keyboard(chat_id))
        elif event.photo:
            os.makedirs(os.path.join("database", "images"), exist_ok=True)
            path = os.path.join("database", "images", f"{chat_id}.jpg")
            await event.download_media(file=path)
            user_data["image_swap_url"] = ""
            user_data["image_swap_path"] = path
            await event.respond("✅ Image override set from your photo!", buttons=get_main_keyboard(chat_id))
        elif text.startswith("http"):
            user_data["image_swap_url"] = text
            user_data["image_swap_path"] = ""
            await event.respond("✅ Image URL override set!", buttons=get_main_keyboard(chat_id))
        else:
            await event.respond("❌ Please send a Photo, a valid URL, or type CLEAR.", buttons=get_main_keyboard(chat_id))
            return
            
        save_user_data(chat_id, user_data)
        user_states[chat_id] = None
        
    # -----------------------------------------------------
    # ADMIN SYSTEM
    # -----------------------------------------------------
    elif state == "waiting_for_broadcast":
        if is_admin(chat_id):
            tenants = get_tenants()
            sent_count = 0
            
            # Send status message first
            status_msg = await event.respond(f"⏳ Broadcasting to {len(tenants)} tenants...")
            
            for tenant_id in tenants:
                try:
                    # By passing event.message, Telethon perfectly copies text, photos, documents, and formatting!
                    await bot.send_message(int(tenant_id), event.message)
                    sent_count += 1
                    # Slight delay to prevent Telegram rate-limiting if there are many tenants
                    await asyncio.sleep(0.5) 
                except Exception:
                    pass
                    
            user_states[chat_id] = None
            await status_msg.edit(f"✅ **Broadcast Complete!**\n\nMessage successfully delivered to {sent_count}/{len(tenants)} tenants.", buttons=get_main_keyboard(chat_id))
            
    elif state == "waiting_for_add_tenant":
        if is_admin(chat_id):
            tenants = get_tenants()
            if text not in tenants:
                tenants.append(text)
                save_tenants(tenants)
                await event.respond(f"✅ Added tenant ID: `{text}`", buttons=get_main_keyboard(chat_id))
                try:
                    await bot.send_message(int(text), "🎉 **Account Activated!**\n\nThe Administrator has just granted you access.\nPlease send /start to open your dashboard!")
                except Exception:
                    pass
            else:
                await event.respond(f"⚠️ Tenant ID `{text}` is already added.", buttons=get_main_keyboard(chat_id))
            user_states[chat_id] = None
            
    elif state == "waiting_for_ai_prompt":
        if is_admin(chat_id):
            status_msg = await event.respond("⏳ Generating professional announcement with Google Gemini...")
            try:
                from google import genai
                client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
                prompt = f"You are a professional marketing manager for a Telegram Bot called Webtgf. Write a highly engaging, hype-building announcement message about this new feature: {text}. Keep it under 150 words. Use emojis. Make it sound exciting."
                response = client.models.generate_content(
                    model='gemini-3.1-flash-lite',
                    contents=prompt,
                )
                
                # Save the generated message in the state so they can approve it
                user_states[chat_id] = {"step": "waiting_for_ai_approval", "message": response.text}
                
                await status_msg.edit(
                    f"**Here is your generated broadcast:**\n\n{response.text}\n\n**Do you want to send this to all tenants?**",
                    buttons=[
                        [Button.inline("✅ Approve & Send", b"ai_approve")],
                        [Button.inline("❌ Cancel", b"admin_panel")]
                    ]
                )
            except Exception as e:
                await status_msg.edit(f"❌ Failed to generate: {e}", buttons=[[Button.inline("🔙 Back", b"admin_panel")]])
            
    elif state == "waiting_for_remove_tenant":
        if is_admin(chat_id):
            tenants = get_tenants()
            if text in tenants:
                tenants.remove(text)
                save_tenants(tenants)
                await event.respond(f"✅ Removed tenant ID: `{text}`", buttons=get_main_keyboard(chat_id))
            else:
                await event.respond(f"❌ Tenant ID `{text}` not found.", buttons=get_main_keyboard(chat_id))
            user_states[chat_id] = None

print("Starting Webtgf Control Bot with OTP capabilities...")
bot.start(bot_token=BOT_TOKEN)
bot.run_until_disconnected()
