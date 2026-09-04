import os
import json
import time
import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import MessageNotModifiedError, SessionPasswordNeededError
from dotenv import load_dotenv, set_key

from database_manager import get_user_data, save_user_data, get_all_users, get_tenants, save_tenants, get_feature_toggles, save_feature_toggles

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
        buttons.append([Button.inline("🛠️ Manual Session Login", b"manual_session")])
        buttons.append([Button.inline("💬 24/7 Support", b"menu_support"), Button.inline("ℹ️ About Us", b"menu_about")])
    else:
        buttons.extend([
            [Button.inline(f"📌 Sources ({len(sources)})", b"menu_sources"), Button.inline(f"🎯 Targets ({len(targets)})", b"menu_targets")],
            [Button.inline("✨ Modification Rules", b"menu_modifications"), Button.inline("🚀 Auto-Posting Suite [PRO 💎]", b"menu_autoposting")],
            [Button.inline("🗑️ Deletion Suite", b"menu_deletion"), Button.inline("📖 How to Use", b"menu_instructions")],
            [Button.inline("⚙️ Settings [PRO 💎]", b"menu_settings"), Button.inline("🔌 Disconnect", b"disconnect_account")],
            [Button.inline("💬 Support", b"menu_support"), Button.inline("ℹ️ About Us", b"menu_about")]
        ])
    
    if is_admin(chat_id):
        buttons.append([Button.inline("👑 Admin Panel", b"admin_panel")])
        
    return buttons
    
async def wait_for_qr_login_task(chat_id, tmp_client, qr_login, msg, api_id, api_hash):
    try:
        await qr_login.wait(120)
    except asyncio.TimeoutError:
        await bot.send_message(chat_id, "❌ QR Code expired. Please try connecting again.")
        await tmp_client.disconnect()
        return
    except SessionPasswordNeededError:
        user_states[chat_id] = {"step": "waiting_for_password"}
        login_sessions[chat_id] = {
            "client": tmp_client,
            "api_id": api_id,
            "api_hash": api_hash,
            "msg_id": msg.id
        }
        await bot.send_message(chat_id, "🔒 **Two-Step Verification Enabled**\n\nPlease enter your Telegram password to complete the QR login:")
        return
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Failed to login via QR: {e}")
        await tmp_client.disconnect()
        return

    # Success
    user_data = get_user_data(chat_id)
    user_data["session_string"] = tmp_client.session.save()
    user_data["api_id"] = api_id
    user_data["api_hash"] = api_hash
    save_user_data(chat_id, user_data)
    user_states[chat_id] = None
    
    await bot.send_message(chat_id, "✅ **Account Successfully Connected via QR Code!**", buttons=get_main_keyboard(chat_id))
    try:
        await bot.delete_messages(chat_id, msg.id)
    except Exception as e:
        pass
    await tmp_client.disconnect()
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
    badge = " 💎 [PRO LIFETIME]" if is_admin(chat_id) else (" 💎 [PRO]" if is_pro(chat_id) else " 🟢 [FREE]")
    
    sender = await event.get_sender()
    name = sender.first_name if sender.first_name else (sender.username if sender.username else "User")
    
    if not user_data.get('session_string'):
        msg = f"👋 Hi, **{name}**! Welcome to the **Webtgf Dashboard**!{badge}\n\nYour forwarding engine is currently **Disconnected**. Please click **🔑 Connect Account** below to securely link your Telegram account and start forwarding messages."
    else:
        msg = f"👋 Hi, **{name}**! Welcome to the **Webtgf Dashboard**!{badge}\n\nManage your forwarding rules, channels, and replacements directly from this menu."
        
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
            badge = " 💎 [PRO LIFETIME]" if is_admin(chat_id) else (" 💎 [PRO]" if is_pro(chat_id) else " 🟢 [FREE]")
            sender = await event.get_sender()
            name = sender.first_name if sender.first_name else (sender.username if sender.username else "User")
            await event.edit(f"👋 Hi, **{name}**! Welcome to the **Webtgf Dashboard**!{badge}", buttons=get_main_keyboard(chat_id))
            return

        # -----------------------------------------------------
        # SETTINGS PANEL & PRO FEATURES
        # -----------------------------------------------------
        elif data == "back_modifications":
            user_states.pop(chat_id, None)
            text = "✨ **Modification Rules**\n\nConfigure how your forwarded messages are edited before they reach the target channels."
            buttons = [
                [Button.inline("🖼 Image Branding [PRO 💎]", b"menu_image"), Button.inline("✏️ Word Swapper", b"menu_words")],
                [Button.inline("🔗 Link & Branding", b"menu_links")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "back_autoposting":
            user_states.pop(chat_id, None)
            user_data = get_user_data(chat_id)
            queue_len = len(user_data.get("drip_queue", []))
            text = f"🚀 **Auto-Posting Suite**\n\nControl the flow of your messages.\n\n**Messages in Queue:** {queue_len}"
            buttons = [
                [Button.inline("🕐 Drip Posting [PRO 💎]", b"menu_drip_posting"), Button.inline("💤 Sleep Mode [PRO 💎]", b"menu_sleep")],
                [Button.inline(f"📥 View Queue ({queue_len})", b"menu_queue")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return
            
        elif data == "menu_modifications":
            text = "✨ **Modification Rules**\n\nConfigure how your forwarded messages are edited before they reach the target channels."
            buttons = [
                [Button.inline("🖼 Image Branding [PRO 💎]", b"menu_image"), Button.inline("✏️ Word Swapper", b"menu_words")],
                [Button.inline("🔗 Link & Branding", b"menu_links")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "menu_autoposting":
            user_data = get_user_data(chat_id)
            queue_len = len(user_data.get("drip_queue", []))
            text = f"🚀 **Auto-Posting Suite**\n\nControl the flow of your messages.\n\n**Messages in Queue:** {queue_len}"
            buttons = [
                [Button.inline("🕐 Drip Posting [PRO 💎]", b"menu_drip_posting"), Button.inline("💤 Sleep Mode [PRO 💎]", b"menu_sleep")],
                [Button.inline(f"📥 View Queue ({queue_len})", b"menu_queue")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "menu_sleep":
            toggles = get_feature_toggles()
            if not toggles.get("sleep_mode_unlocked", False) and not is_admin(chat_id):
                await event.answer("👨‍🍳 Still cooking... This feature is locked by the Admin.", alert=True)
                return
                
            user_data = get_user_data(chat_id)
            sleep_mode = user_data.get("sleep_mode", {})
            
            is_enabled = sleep_mode.get("enabled", False)
            start_t = sleep_mode.get("start_time", "22:00")
            end_t = sleep_mode.get("end_time", "08:00")
            offset = sleep_mode.get("timezone_offset", 0)
            
            status = "✅ ON" if is_enabled else "❌ OFF"
            text = (
                "💤 **Sleep Mode / Blackout Window**\n\n"
                "Hold all incoming messages during specific hours and drip them out in the morning.\n\n"
                f"**Status:** {status}\n"
                f"**Start Time:** {start_t}\n"
                f"**End Time:** {end_t}\n"
                f"**Timezone Offset (UTC):** {offset}\n\n"
                "Use the buttons below to configure your sleep window."
            )
            buttons = [
                [Button.inline("Toggle ON/OFF", b"sleep_toggle")],
                [Button.inline("✏️ Edit Times", b"sleep_edit")],
                [Button.inline("🔙 Back", b"back_autoposting")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "sleep_toggle":
            user_data = get_user_data(chat_id)
            sleep_mode = user_data.get("sleep_mode", {})
            sleep_mode["enabled"] = not sleep_mode.get("enabled", False)
            user_data["sleep_mode"] = sleep_mode
            save_user_data(chat_id, user_data)
            await event.answer("Sleep Mode toggled!", alert=False)
            
            # Refresh menu
            is_enabled = sleep_mode.get("enabled", False)
            start_t = sleep_mode.get("start_time", "22:00")
            end_t = sleep_mode.get("end_time", "08:00")
            offset = sleep_mode.get("timezone_offset", 0)
            status = "✅ ON" if is_enabled else "❌ OFF"
            text = (
                "💤 **Sleep Mode / Blackout Window**\n\n"
                "Hold all incoming messages during specific hours and drip them out in the morning.\n\n"
                f"**Status:** {status}\n"
                f"**Start Time:** {start_t}\n"
                f"**End Time:** {end_t}\n"
                f"**Timezone Offset (UTC):** {offset}\n\n"
                "Use the buttons below to configure your sleep window."
            )
            buttons = [
                [Button.inline("Toggle ON/OFF", b"sleep_toggle")],
                [Button.inline("✏️ Edit Times", b"sleep_edit")],
                [Button.inline("🔙 Back", b"back_autoposting")]
            ]
            await event.edit(text, buttons=buttons)
            return
            
        elif data == "sleep_edit":
            user_states[chat_id] = {"step": "waiting_for_sleep_settings"}
            await event.edit(
                "✏️ **Edit Sleep Settings**\n\n"
                "Please reply with your settings in this exact format:\n"
                "`[Start Time] - [End Time] - [UTC Offset]`\n\n"
                "**Example:**\n"
                "`22:00 - 08:00 - -5`\n"
                "*(This means 10 PM to 8 AM in EST timezone)*\n\n"
                "**Example 2 (London/UTC):**\n"
                "`23:00 - 07:00 - 0`\n\n"
                "Please reply with your times (24-hour format):",
                buttons=[[Button.inline("🔙 Cancel", b"back_autoposting")]]
            )
            return

        elif data == "menu_queue":
            user_data = get_user_data(chat_id)
            queue = user_data.get("drip_queue", [])
            
            if not queue:
                await event.edit("📥 **Message Queue**\n\nYour queue is currently empty.", buttons=[[Button.inline("🔙 Back", b"back_autoposting")]])
                return
                
            text = f"📥 **Message Queue** ({len(queue)} messages)\n\n"
            for i, q in enumerate(queue[:10]):
                text += f"**{i+1}.** {q.get('preview', '[Media]')}\n"
                
            if len(queue) > 10:
                text += f"\n*...and {len(queue)-10} more.*"
                
            buttons = [
                [Button.inline("▶️ Forward All Now", b"queue_forward_all")],
                [Button.inline("❌ Cancel All", b"queue_clear")],
                [Button.inline("🔙 Back", b"back_autoposting")]
            ]
            await event.edit(text, buttons=buttons)
            return
            
        elif data == "queue_forward_all":
            user_data = get_user_data(chat_id)
            user_data["drip_interval"] = 0
            user_data["sleep_mode"] = user_data.get("sleep_mode", {})
            user_data["sleep_mode"]["enabled"] = False
            save_user_data(chat_id, user_data)
            await event.answer("Queue flushing initiated! Sleep mode & Drip interval have been disabled to allow instant sending.", alert=True)
            await event.edit("✅ **Queue Flushed**\n\nAll messages will be sent momentarily.", buttons=[[Button.inline("🔙 Back", b"back_autoposting")]])
            return
            
        elif data == "queue_clear":
            user_data = get_user_data(chat_id)
            user_data["drip_queue"] = []
            save_user_data(chat_id, user_data)
            await event.answer("Queue cleared!", alert=True)
            await event.edit("🗑️ **Queue Cleared**\n\nAll held messages have been deleted.", buttons=[[Button.inline("🔙 Back", b"back_autoposting")]])
            return

        elif data == "menu_drip_posting":
            toggles = get_feature_toggles()
            if not toggles.get("drip_posting_unlocked", False) and not is_admin(chat_id):
                await event.answer("👨‍🍳 Still cooking... This feature is locked by the Admin.", alert=True)
                return
                
            user_data = get_user_data(chat_id)
            interval = user_data.get("drip_interval", 0)
            queue_len = len(user_data.get("drip_queue", []))
            
            if interval > 0:
                if interval < 60:
                    readable = f"{interval} seconds"
                elif interval % 60 == 0:
                    readable = f"{interval // 60} minute(s)"
                else:
                    readable = f"{interval // 60}m {interval % 60}s"
                status = f"✅ ON (every {readable})"
            else:
                status = "❌ OFF"
            text = (
                "🕒 **Drip Posting (Pro Feature)**\n\n"
                "Instead of forwarding messages instantly, Drip Posting queues them and sends one by one at your chosen interval.\n\n"
                f"**Status:** {status}\n"
                f"**Messages in Queue:** {queue_len}\n\n"
                "👇 **Pick how often you want to post:**"
            )
            buttons = [
                [Button.inline("⚡ 30 seconds", b"drip_30"), Button.inline("⏱ 1 minute", b"drip_60")],
                [Button.inline("🕑 2 minutes", b"drip_120"), Button.inline("🕔 5 minutes", b"drip_300")],
                [Button.inline("🕙 10 minutes", b"drip_600"), Button.inline("🕧 30 minutes", b"drip_1800")],
                [Button.inline("🕐 1 hour", b"drip_3600"), Button.inline("✏️ Custom (seconds)", b"drip_custom")],
                [Button.inline("❌ Disable Drip", b"drip_0")],
                [Button.inline("🔙 Back", b"back_autoposting")],
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data.startswith("drip_"):
            val = data[5:]  # e.g. "30", "60", "0", "custom"
            user_data = get_user_data(chat_id)

            if val == "custom":
                user_states[chat_id] = {"step": "waiting_for_drip"}
                await event.edit(
                    "✏️ **Custom Drip Interval**\n\nType the number of **seconds** you want between each post.\n\nExamples:\n• `10` = 10 seconds\n• `90` = 1 min 30 sec\n• `3600` = 1 hour",
                    buttons=[[Button.inline("🔙 Cancel", b"menu_drip_posting")]]
                )
                return

            seconds = int(val)
            user_data["drip_interval"] = seconds
            if seconds == 0:
                user_data["drip_queue"] = []
                msg = "❌ Drip Posting has been **DISABLED**. Messages will now forward instantly."
            else:
                if seconds < 60:
                    readable = f"{seconds} seconds"
                elif seconds % 60 == 0:
                    readable = f"{seconds // 60} minute(s)"
                else:
                    readable = f"{seconds // 60}m {seconds % 60}s"
                msg = f"✅ Drip Posting **ENABLED**! One message will be sent every **{readable}**."
            save_user_data(chat_id, user_data)
            await event.answer(msg, alert=True)
            # Refresh the drip menu
            queue_len = len(user_data.get("drip_queue", []))
            interval = seconds
            if interval > 0:
                if interval < 60:
                    readable = f"{interval} seconds"
                elif interval % 60 == 0:
                    readable = f"{interval // 60} minute(s)"
                else:
                    readable = f"{interval // 60}m {interval % 60}s"
                status = f"✅ ON (every {readable})"
            else:
                status = "❌ OFF"
            text = (
                "🕒 **Drip Posting (Pro Feature)**\n\n"
                "Instead of forwarding messages instantly, Drip Posting queues them and sends one by one at your chosen interval.\n\n"
                f"**Status:** {status}\n"
                f"**Messages in Queue:** {queue_len}\n\n"
                "👇 **Pick how often you want to post:**"
            )
            buttons = [
                [Button.inline("⚡ 30 seconds", b"drip_30"), Button.inline("⏱ 1 minute", b"drip_60")],
                [Button.inline("🕑 2 minutes", b"drip_120"), Button.inline("🕔 5 minutes", b"drip_300")],
                [Button.inline("🕙 10 minutes", b"drip_600"), Button.inline("🕧 30 minutes", b"drip_1800")],
                [Button.inline("🕐 1 hour", b"drip_3600"), Button.inline("✏️ Custom (seconds)", b"drip_custom")],
                [Button.inline("❌ Disable Drip", b"drip_0")],
                [Button.inline("🔙 Back", b"back_autoposting")],
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "menu_deletion":
            toggles = get_feature_toggles()
            if not toggles.get("deletion_unlocked", False) and not is_admin(chat_id):
                await event.answer("👨‍🍳 Still cooking... This feature is locked by the Admin.", alert=True)
                return
                
            user_data = get_user_data(chat_id)
            pin = user_data.get("deletion_pin", None)
            mirror = user_data.get("mirror_delete", False)
            auto_limit = user_data.get("auto_delete_limit", 0)
            
            status_mirror = "✅ ON" if mirror else "❌ OFF"
            status_limit = f"Keep Last {auto_limit}" if auto_limit > 0 else "❌ OFF"
            status_pin = "✅ SET" if pin else "❌ NOT SET"
            
            text = (
                "🗑️ **Deletion Suite (Pro Feature)**\n\n"
                "Manage how the bot deletes messages in your Target channels.\n\n"
                f"**1. Mirror Delete:** {status_mirror}\n"
                "*(If a message is deleted in the Source channel, delete it in the Target channel too.)*\n\n"
                f"**2. Auto-Delete Limit:** {status_limit}\n"
                "*(Rolling Window: automatically delete older messages to keep the channel clean.)*\n\n"
                f"**3. Security PIN:** {status_pin}\n"
                "*(Required to execute manual wipes to prevent accidental data loss.)*\n\n"
                "👇 **Select an option below:**"
            )
            
            buttons = [
                [Button.inline(f"🪞 Mirror Delete: {'✅' if mirror else '❌'}", b"del_toggle_mirror"), Button.inline("⏱️ Auto-Delete Limit", b"del_set_limit")],
                [Button.inline("🔐 Set Security PIN", b"del_set_pin"), Button.inline("🗑️ Wipe: Last 10", b"wipe_10")],
                [Button.inline("💣 Wipe: Last 50", b"wipe_50"), Button.inline("📅 Wipe: Today", b"wipe_today")],
                [Button.inline("🔙 Back", b"back")]
            ]
            
            await event.edit(text, buttons=buttons)
            return

        elif data == "del_toggle_mirror":
            user_data = get_user_data(chat_id)
            user_data["mirror_delete"] = not user_data.get("mirror_delete", False)
            save_user_data(chat_id, user_data)
            
            # Re-render menu directly
            pin = user_data.get("deletion_pin", None)
            mirror = user_data.get("mirror_delete", False)
            auto_limit = user_data.get("auto_delete_limit", 0)
            status_mirror = "✅ ON" if mirror else "❌ OFF"
            status_limit = f"Keep Last {auto_limit}" if auto_limit > 0 else "❌ OFF"
            status_pin = "✅ SET" if pin else "❌ NOT SET"
            text = (
                "🗑️ **Deletion Suite (Pro Feature)**\n\n"
                "Manage how the bot deletes messages in your Target channels.\n\n"
                f"**1. Mirror Delete:** {status_mirror}\n"
                "*(If a message is deleted in the Source channel, delete it in the Target channel too.)*\n\n"
                f"**2. Auto-Delete Limit:** {status_limit}\n"
                "*(Rolling Window: automatically delete older messages to keep the channel clean.)*\n\n"
                f"**3. Security PIN:** {status_pin}\n"
                "*(Required to execute manual wipes to prevent accidental data loss.)*\n\n"
                "👇 **Select an option below:**"
            )
            buttons = [
                [Button.inline(f"🪞 Mirror Delete: {'✅' if mirror else '❌'}", b"del_toggle_mirror"), Button.inline("⏱️ Auto-Delete Limit", b"del_set_limit")],
                [Button.inline("🔐 Set Security PIN", b"del_set_pin"), Button.inline("🗑️ Wipe: Last 10", b"wipe_10")],
                [Button.inline("💣 Wipe: Last 50", b"wipe_50"), Button.inline("📅 Wipe: Today", b"wipe_today")],
                [Button.inline("🔙 Back", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return
            
        elif data == "del_set_limit":
            user_states[chat_id] = {"step": "waiting_for_del_limit"}
            await event.edit(
                "⏱️ **Auto-Delete Limit (Rolling Window)**\n\n"
                "How many messages do you want to keep in the Target channel? If you type `50`, the bot will automatically delete the oldest message whenever the 51st message is forwarded.\n\n"
                "Type a number (e.g., `50`). Type `0` to disable.",
                buttons=[[Button.inline("🔙 Cancel", b"menu_deletion")]]
            )
            return
            
        elif data == "del_set_pin":
            user_states[chat_id] = {"step": "waiting_for_new_pin"}
            await event.edit(
                "🔐 **Set Security PIN**\n\n"
                "Please reply with a 4-digit PIN (e.g., `1234`). You will need this PIN to authorize any manual message wipes.",
                buttons=[[Button.inline("🔙 Cancel", b"menu_deletion")]]
            )
            return
            
        elif data.startswith("wipe_"):
            val = data[5:]
            user_data = get_user_data(chat_id)
            if not user_data.get("deletion_pin"):
                await event.answer("❌ You must set a Security PIN first!", alert=True)
                return
                
            user_states[chat_id] = {"step": "waiting_for_wipe_pin", "wipe_type": val}
            await event.edit(
                f"⚠️ **AUTHORIZATION REQUIRED** ⚠️\n\n"
                f"You are about to execute a manual wipe: `{val}`\n\n"
                "Please enter your 4-digit Security PIN to confirm this destructive action.",
                buttons=[[Button.inline("🔙 Cancel", b"menu_deletion")]]
            )
            return

        elif data == "menu_instructions":
            text = (
                "📖 **How To Use This Bot (Step-by-Step Guide)**\n\n"
                "Welcome! Listen carefully, let's break down how this bot works so you can start forwarding your messages sharp sharp without any stress.\n\n"
                "Select a topic below to read the step-by-step guide for it:"
            )
            buttons = [
                [Button.inline("📲 1. How to Connect Account", b"inst_connect")],
                [Button.inline("🎯 2. Sources & Targets", b"inst_channels")],
                [Button.inline("✨ 3. Modifying Messages", b"inst_modify")],
                [Button.inline("🚀 4. Auto-Posting (Drip/Sleep)", b"inst_auto")],
                [Button.inline("⚙️ 5. Advanced & AI Features", b"inst_advanced")],
                [Button.inline("🔙 Back to Main Menu", b"back")]
            ]
            await event.edit(text, buttons=buttons)
            return

        elif data == "inst_connect":
            text = (
                "📲 **Step 1: Connecting Your Account**\n\n"
                "First things first, the bot needs to use your Telegram account to read messages and forward them for you.\n\n"
                "**How to do it:**\n"
                "1. On the Main Menu, click on **Connect Account**.\n"
                "2. Enter your phone number (including country code, e.g., +234...).\n"
                "3. Telegram will send a login code to your Telegram app.\n"
                "4. Type the code here in the bot. (If you have a 2-Step Verification password, the bot will ask for it).\n\n"
                "Once connected, your status will change to ✅ Connected. Now you are ready for action!"
            )
            buttons = [[Button.inline("🔙 Back to Instructions", b"menu_instructions")]]
            await event.edit(text, buttons=buttons)
            return

        elif data == "inst_channels":
            text = (
                "🎯 **Step 2: Adding Sources and Targets**\n\n"
                "This is where you tell the bot where to copy messages *from* (Source) and where to paste them *to* (Target).\n\n"
                "**How to add them:**\n"
                "1. Click **Sources** or **Targets** on the main menu.\n"
                "2. Go to the channel you want to add, and **forward any message** from it to this bot.\n"
                "3. **What if forwarding is blocked?** No shaking! Just copy any post link from the channel (like https://t.me/c/12345/67) and paste it to the bot. It will extract the ID automatically!\n"
                "4. You can also just type the @username of the channel.\n\n"
                "**To Remove a channel:** Just forward a message from it again, and the bot will remove it from your list. Sharp sharp!"
            )
            buttons = [[Button.inline("🔙 Back to Instructions", b"menu_instructions")]]
            await event.edit(text, buttons=buttons)
            return

        elif data == "inst_modify":
            text = (
                "✨ **Step 3: Modifying Your Messages**\n\n"
                "You don't want to just forward messages raw. You want to brand them as your own! Click **Modification Rules** on the main menu to set this up.\n\n"
                "• **✏️ Word Swapper**: Did the source channel type their name? Tell the bot to swap their name to your own name automatically!\n"
                "• **🖼 Image Branding**: You can set a custom photo. If the source posts a picture, the bot will remove their picture and attach your own promotional picture instead. *(Videos & GIFs are completely untouched!)*\n"
                "• **🔗 Link Replacement**: The bot replaces links with your own referral link. You can also set **Excluded Links** (e.g. `EXCLUDE=redbagCode, gift`) so it completely ignores and preserves special casino or giveaway links!"
            )
            buttons = [[Button.inline("🔙 Back to Instructions", b"menu_instructions")]]
            await event.edit(text, buttons=buttons)
            return

        elif data == "inst_auto":
            text = (
                "🚀 **Step 4: Auto-Posting Suite**\n\n"
                "Don't just dump 20 messages into your channel at once, it will annoy your subscribers. Manage the flow!\n\n"
                "• **🕐 Drip Posting**: Holds your forwarded messages in a queue, and releases them one by one based on the time interval you set (e.g., every 5 minutes). Keeps your channel active all day!\n"
                "• **💤 Sleep Mode**: Set your sleeping time (e.g., 10:00 PM to 7:00 AM). The bot will hold all messages that arrive in the night. Once you wake up by 7:00 AM, it will start dripping them automatically.\n\n"
                "You can always check your held messages in the **📥 View Queue** menu."
            )
            buttons = [[Button.inline("🔙 Back to Instructions", b"menu_instructions")]]
            await event.edit(text, buttons=buttons)
            return
            
        elif data == "inst_advanced":
            text = (
                "⚙️ **Step 5: Advanced & AI Features**\n\n"
                "The bot has powerful features hidden in the **Advanced Settings** and **AI Watermark** menus!\n\n"
                "• **🚫 Restricted Channel Bypass**: If the source channel has 'Restrict Saving Content' ON, the bot will automatically defeat it by silently downloading the video/image to memory and re-uploading it to your target.\n"
                "• **💵 Anti-Payment Stripper**: Automatically scans and deletes BTC, ETH, USDT, SOL, and Bank Account (Kuda, Opay, etc.) details from forwarded messages.\n"
                "• **⏱ Smart Delay**: Delays forwarding by 1 to 3 minutes to mimic human behavior and avoid Telegram spam bans.\n"
                "• **🤖 AI Watermark Generator**: Automatically converts incoming photos into stunning promotional banners with your target text embedded right inside the image!"
            )
            buttons = [[Button.inline("🔙 Back to Instructions", b"menu_instructions")]]
            await event.edit(text, buttons=buttons)
            return

        elif data in ("menu_settings", "toggle_smart_delay", "toggle_anti_payment"):
            user_data = get_user_data(chat_id)
            
            if data == "toggle_smart_delay":
                user_data["smart_delay_enabled"] = not user_data.get("smart_delay_enabled", False)
                save_user_data(chat_id, user_data)
                status = "✅ ON" if user_data["smart_delay_enabled"] else "❌ OFF"
                await event.answer(f"Smart Delay turned {status}!", alert=True)
                
            elif data == "toggle_anti_payment":
                user_data["strip_payment_details"] = not user_data.get("strip_payment_details", False)
                save_user_data(chat_id, user_data)
                status = "✅ ON" if user_data["strip_payment_details"] else "❌ OFF"
                await event.answer(f"Anti-Payment Stripper turned {status}!", alert=True)
                
            delay_enabled = user_data.get("smart_delay_enabled", False)
            strip_enabled = user_data.get("strip_payment_details", False)
            
            d_status = "✅ ON" if delay_enabled else "❌ OFF"
            s_status = "✅ ON" if strip_enabled else "❌ OFF"
            
            text = (
                "⚙️ **Advanced Settings Panel**\n\n"
                "**1. Smart Delay (Anti-Ban)**\n"
                "If enabled, the bot will wait 1 to 3 minutes before forwarding, making it look like a real human.\n"
                f"Current Status: {d_status}\n\n"
                "**2. Anti-Payment Stripper**\n"
                "If enabled, the bot will automatically delete any Crypto addresses (BTC, ETH, USDT) and Bank Account numbers from the text before forwarding.\n"
                f"Current Status: {s_status}"
            )
            
            buttons = [
                [Button.inline(f"Smart Delay [PRO 💎]: {d_status}", b"toggle_smart_delay")],
                [Button.inline(f"Anti-Payment Stripper [PRO 💎]: {s_status}", b"toggle_anti_payment")],
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
            
        elif data == "login_phone":
            user_states[chat_id]["step"] = "waiting_for_phone"
            await event.edit(
                "Perfect. Now reply with your **Phone Number** (including the country code, e.g., `+1234567890`).", 
                buttons=[[Button.inline("🔙 Cancel", b"back")]]
            )
            return
            
        elif data == "login_qr":
            state = user_states.get(chat_id)
            if not state or "api_id" not in state:
                await event.answer("❌ Session expired. Please start over.", alert=True)
                return
                
            user_states[chat_id]["step"] = "waiting_for_qr"
            await event.edit("⏳ Generating QR code, please wait...")
            
            import qrcode
            import io
            
            try:
                tmp_client = TelegramClient(StringSession(), state["api_id"], state["api_hash"])
                await tmp_client.connect()
                qr_login = await tmp_client.qr_login()
                
                # generate qr image
                img = qrcode.make(qr_login.url)
                bio = io.BytesIO()
                bio.name = 'qr.png'
                img.save(bio, 'PNG')
                bio.seek(0)
                
                msg = await event.respond(
                    "📱 **Scan this QR Code**\n\n"
                    "1. Open Telegram on your phone\n"
                    "2. Go to **Settings** > **Devices**\n"
                    "3. Tap **Link Desktop Device** and scan this code.",
                    file=bio,
                    buttons=[[Button.inline("🔙 Cancel", b"back")]]
                )
                
                # We can't wait here because it blocks the callback loop. 
                # We'll spawn an asyncio task.
                asyncio.create_task(wait_for_qr_login_task(chat_id, tmp_client, qr_login, msg, state["api_id"], state["api_hash"]))
                
            except Exception as e:
                await event.respond(f"❌ Failed to generate QR: {e}")
            return
            
        elif data == "manual_session":
            user_states[chat_id] = {"step": "waiting_for_manual_session"}
            await event.edit(
                "🛠️ **Manual Session Login**\n\n"
                "If Telegram is blocking SMS/App codes from this server, you can generate a session locally on your own PC and paste it here.\n\n"
                "Please reply with your `StringSession` (the long block of letters/numbers).",
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
            
        elif data == "resend_code":
            session_data = login_sessions.get(chat_id)
            if not session_data:
                await event.answer("❌ Session expired. Please start over.", alert=True)
                return
                
            tmp_client = session_data["client"]
            phone = session_data["phone"]
            
            try:
                res = await tmp_client.send_code_request(phone)
                session_data["phone_code_hash"] = res.phone_code_hash
                login_sessions[chat_id] = session_data
                
                delivery_method = str(type(res.type).__name__)
                where = "your Telegram App"
                if "Sms" in delivery_method:
                    where = "an SMS text message"
                elif "Call" in delivery_method:
                    where = "a Phone Call"
                    
                await event.respond(f"✅ Code resent via {where}!")
            except Exception as e:
                await event.respond(f"❌ Failed to resend: {e}")
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
                "👉 **How to add or remove a source:**\n"
                "Simply **Forward any message** from the channel to me here!\n"
                "*(Forwarding a channel that is already in your list will remove it.)*\n"
                "*(Or manually reply with a `@username`, `-100` ID, or a private post link like `https://t.me/c/1234...`)*\n\n"
                "Send /cancel to go back, or type CLEAR to remove all.",
                buttons=[[Button.inline("🔙 Back", b"back")]]
            )
            
        elif data == "menu_targets":
            user_states[chat_id] = "waiting_for_targets"
            current = ", ".join(user_data.get('targets', []))
            await event.edit(
                f"**🎯 Edit Targets**\n\nCurrent Targets:\n`{current}`\n\n"
                "👉 **How to add or remove a target:**\n"
                "Simply **Forward any message** from the channel to me here!\n"
                "*(Forwarding a channel that is already in your list will remove it.)*\n"
                "*(Or manually reply with a list of `@username`, `-100` IDs, or `https://t.me/c/...` links)*\n\n"
                "Send /cancel to go back, or type CLEAR to remove all.",
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
            await event.edit(msg, buttons=[[Button.inline("🔙 Back", b"back_modifications")]])
    
        elif data == "menu_links":
            user_states[chat_id] = "waiting_for_link"
            current_link = user_data.get("replace_all_links_with", "")
            current_user = user_data.get("replace_all_usernames_with", "")
            current_exclude = user_data.get("exclude_link_keywords", "")
            await event.edit(
                f"**🔗 Link & Branding**\n\n"
                f"Global Link: `{current_link}`\n"
                f"Global Username: `{current_user}`\n"
                f"Excluded Links: `{current_exclude}`\n\n"
                f"Reply with:\n"
                f"`LINK=https://yourlink.com`\n"
                f"`USER=@youruser`\n"
                f"`EXCLUDE=redbagCode, gift` (Do not replace links containing these words)",
                buttons=[[Button.inline("🔙 Back", b"back_modifications")]]
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
                f"**🖼 Image Branding**\n\n"
                f"📸 **Image Overwrite:** `{status}`\nStatus: {'**ENABLED**' if is_enabled else '**DISABLED**'}\n\n"
                "👉 **How to set a global overwrite image:**\n"
                "Simply **Send a Photo** to the bot right now!\n"
                "*(Or manually reply with a direct image URL, or type `CLEAR` to remove it)*\n\n"
                "---\n"
                "🤖 **AI Watermark Tools (Pro)**\n"
                "Automatically hunt and remove/replace competitor text on images!",
                buttons=[
                    [Button.inline(toggle_btn, b"toggle_image")],
                    [Button.inline("🪄 AI Watermark Remover [PRO 💎]", b"ai_watermark_remover")],
                    [Button.inline("✍️ AI Watermark Replacer [PRO 💎]", b"ai_watermark_replacer")],
                    [Button.inline("🔙 Back", b"back_modifications")]
                ]
            )
            
        elif data == "ai_watermark_remover":
            toggles = get_feature_toggles()
            if not toggles.get("ai_watermark_unlocked", False) and not is_admin(chat_id):
                await event.answer("👨‍🍳 Still cooking... This feature is locked by the Admin.", alert=True)
                return
            user_states[chat_id] = "waiting_for_watermark_remove"
            await event.edit(
                "🪄 **AI Watermark Remover**\n\n"
                "The AI will scan incoming images, find the text you specify, and automatically blend it out to remove it.\n\n"
                "**What text should the AI hunt for?**\n"
                "*(e.g., `Earn with Nazzy`)*\n\n"
                "Reply with the text, or type `CLEAR` to disable.",
                buttons=[[Button.inline("🔙 Cancel", b"menu_image")]]
            )
            return

        elif data == "ai_watermark_replacer":
            toggles = get_feature_toggles()
            if not toggles.get("ai_watermark_unlocked", False) and not is_admin(chat_id):
                await event.answer("👨‍🍳 Still cooking... This feature is locked by the Admin.", alert=True)
                return
            user_states[chat_id] = "waiting_for_watermark_replace"
            await event.edit(
                "✍️ **AI Watermark Replacer**\n\n"
                "The AI will scan incoming images, find a competitor's text, and overwrite it with YOUR text!\n\n"
                "**Reply in this format:**\n"
                "`OldText | NewText`\n\n"
                "*(e.g., `Earn with Nazzy | Earn with Webtgf`)*\n\n"
                "Reply with the text, or type `CLEAR` to disable.",
                buttons=[[Button.inline("🔙 Cancel", b"menu_image")]]
            )
            return

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
                [Button.inline("💎 Manage PRO Users", b"admin_manage_pro")],
                [Button.inline("➕ Add Tenant", b"admin_add"), Button.inline("➖ Remove Tenant", b"admin_remove")],
                [Button.inline("👥 View Tenants", b"admin_view"), Button.inline("📊 Analytics", b"admin_analytics")],
                [Button.inline("⚙️ Feature Toggles", b"admin_features")],
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
            pro_count = 0
            for t in tenants:
                if get_user_data(t).get("is_pro", False) or is_admin(t):
                    pro_count += 1
            free_count = len(tenants) - pro_count
            
            msg = (
                "📊 **Webtgf Analytics Dashboard**\n\n"
                f"👥 **Total Tenants:** `{len(tenants)}`\n"
                f"💎 **Total PRO Users:** `{pro_count}`\n"
                f"🟢 **Total FREE Users:** `{free_count}`\n\n"
                f"📈 **Total Messages Forwarded:** `{stats['total']}`\n"
                f"🔥 **Messages Forwarded Today:** `{stats['today']}`\n"
            )
            await event.edit(msg, buttons=[[Button.inline("🔙 Back", b"admin_panel")]])
            
        elif data == "admin_features" and is_admin(chat_id):
            toggles = get_feature_toggles()
            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            sleep_locked = not toggles.get("sleep_mode_unlocked", False)
            
            del_locked = not toggles.get("deletion_unlocked", False)
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            sleep_btn_text = "🔓 Unlock Sleep Mode" if sleep_locked else "🔒 Lock Sleep Mode"
            del_btn_text = "🔓 Unlock Deletion Suite" if del_locked else "🔒 Lock Deletion Suite"
            
            await event.edit(
                "🎛️ **Admin Feature Toggles**\n\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline(sleep_btn_text, b"toggle_admin_sleep")],
                    [Button.inline(del_btn_text, b"toggle_admin_del")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )
            

        elif data in ("toggle_admin_drip", "toggle_admin_ai", "toggle_admin_sleep", "toggle_admin_del") and is_admin(chat_id):
            toggles = get_feature_toggles()
            if data == "toggle_admin_drip":
                toggles["drip_posting_unlocked"] = not toggles.get("drip_posting_unlocked", False)
            elif data == "toggle_admin_ai":
                toggles["ai_watermark_unlocked"] = not toggles.get("ai_watermark_unlocked", False)
            elif data == "toggle_admin_sleep":
                toggles["sleep_mode_unlocked"] = not toggles.get("sleep_mode_unlocked", False)
            elif data == "toggle_admin_del":
                toggles["deletion_unlocked"] = not toggles.get("deletion_unlocked", False)
            save_feature_toggles(toggles)

            drip_locked = not toggles.get("drip_posting_unlocked", False)
            ai_locked = not toggles.get("ai_watermark_unlocked", False)
            sleep_locked = not toggles.get("sleep_mode_unlocked", False)
            del_locked = not toggles.get("deletion_unlocked", False)
            btn_text = "🔓 Unlock Drip Posting" if drip_locked else "🔒 Lock Drip Posting"
            ai_btn_text = "🔓 Unlock AI Watermark" if ai_locked else "🔒 Lock AI Watermark"
            sleep_btn_text = "🔓 Unlock Sleep Mode" if sleep_locked else "🔒 Lock Sleep Mode"
            del_btn_text = "🔓 Unlock Deletion Suite" if del_locked else "🔒 Lock Deletion Suite"

            await event.edit(
                "🎛️ **Admin Feature Toggles**\n\nLock or unlock features for all tenants.",
                buttons=[
                    [Button.inline(btn_text, b"toggle_admin_drip")],
                    [Button.inline(ai_btn_text, b"toggle_admin_ai")],
                    [Button.inline(sleep_btn_text, b"toggle_admin_sleep")],
                    [Button.inline(del_btn_text, b"toggle_admin_del")],
                    [Button.inline("🔙 Back", b"admin_panel")]
                ]
            )

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
            
        elif data == "admin_manage_pro" and is_admin(chat_id):
            user_states[chat_id] = "waiting_for_pro_id"
            await event.edit(
                "💎 **Manage PRO Users**\n\n"
                "To Grant or Revoke PRO status, please reply with the user's Telegram ID.\n\n"
                "*(You can get their ID from the 'View Tenants' menu)*",
                buttons=[[Button.inline("🔙 Back to Admin", b"admin_panel")]]
            )
            return
            
        elif data == "admin_view" and is_admin(chat_id):
            tenants = get_tenants()
            msg = "👥 **Current Tenants:**\n\n"
            if not tenants:
                msg += "No tenants added yet."
            else:
                for t in tenants:
                    badge = " 💎 PRO" if (get_user_data(t).get("is_pro", False) or is_admin(t)) else " 🟢 FREE"
                    msg += f"• `{t}`{badge}\n"
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
    if state == "waiting_for_watermark_remove":
        if text.upper() == "CLEAR":
            user_data["ai_watermark_mode"] = "off"
            user_data["ai_watermark_target"] = ""
            user_data["ai_watermark_replace"] = ""
            await event.respond("✅ AI Watermark tools disabled.", buttons=get_main_keyboard(chat_id))
        else:
            user_data["ai_watermark_mode"] = "remove"
            user_data["ai_watermark_target"] = text.strip()
            await event.respond(f"✅ Active! The AI will now hunt for `{text}` and remove it from images.", buttons=get_main_keyboard(chat_id))
        
        save_user_data(chat_id, user_data)
        user_states[chat_id] = None
        
    elif state == "waiting_for_watermark_replace":
        if text.upper() == "CLEAR":
            user_data["ai_watermark_mode"] = "off"
            user_data["ai_watermark_target"] = ""
            user_data["ai_watermark_replace"] = ""
            await event.respond("✅ AI Watermark tools disabled.", buttons=get_main_keyboard(chat_id))
        else:
            if "|" not in text:
                await event.respond("❌ Please use the format: `OldText | NewText`")
                return
                
            parts = text.split("|")
            old_t = parts[0].strip()
            new_t = parts[1].strip()
            
            user_data["ai_watermark_mode"] = "replace"
            user_data["ai_watermark_target"] = old_t
            user_data["ai_watermark_replace"] = new_t
            await event.respond(f"✅ Active! The AI will now hunt for `{old_t}` and replace it with `{new_t}`.", buttons=get_main_keyboard(chat_id))
            
        save_user_data(chat_id, user_data)
        user_states[chat_id] = None
        
    elif isinstance(state, dict):
        step = state.get("step")
        
        # --- DRIP POSTING ---
        if step == "waiting_for_drip":
            if not text.isdigit():
                await event.respond("❌ Please enter a valid number in seconds (e.g., 30 for 30 seconds, 300 for 5 minutes).")
                return
                
            interval = int(text)
            user_data = get_user_data(chat_id)
            user_data["drip_interval"] = interval
            if interval == 0:
                user_data["drip_queue"] = [] # Clear queue if disabled
            save_user_data(chat_id, user_data)
            
            if interval > 0:
                if interval < 60:
                    readable = f"{interval} seconds"
                elif interval % 60 == 0:
                    readable = f"{interval // 60} minute(s)"
                else:
                    readable = f"{interval // 60}m {interval % 60}s"
                status = f"✅ Drip Posting ENABLED! Messages will be queued and sent every {readable}."
            else:
                status = "❌ Drip Posting DISABLED."
            await event.respond(status, buttons=get_main_keyboard(chat_id))
            user_states[chat_id] = None
            return

        # --- LOGIN STEPS ---
        elif step == "waiting_for_new_pin":
            if not text.isdigit() or len(text) != 4:
                await event.respond("❌ Invalid PIN. Please enter exactly 4 digits (e.g. 1234).")
                return
            user_data = get_user_data(chat_id)
            user_data["deletion_pin"] = text
            save_user_data(chat_id, user_data)
            await event.respond("✅ **Security PIN Set Successfully!**\n\nYou can now execute manual wipes.", buttons=get_main_keyboard(chat_id))
            user_states[chat_id] = None
            return
            
        elif step == "waiting_for_del_limit":
            if not text.isdigit():
                await event.respond("❌ Invalid limit. Please enter a valid number (e.g. 50).")
                return
            limit = int(text)
            user_data = get_user_data(chat_id)
            user_data["auto_delete_limit"] = limit
            save_user_data(chat_id, user_data)
            
            if limit > 0:
                await event.respond(f"✅ **Auto-Delete Limit Set!**\n\nThe bot will now keep exactly {limit} messages in your Target channels. Older messages will be deleted automatically as new ones arrive.", buttons=get_main_keyboard(chat_id))
            else:
                await event.respond("✅ **Auto-Delete Limit Disabled!**", buttons=get_main_keyboard(chat_id))
                
            user_states[chat_id] = None
            return
            
        elif step == "waiting_for_wipe_pin":
            try: await event.message.delete()
            except: pass
            user_data = get_user_data(chat_id)
            pin = user_data.get("deletion_pin")
            if text != pin:
                await event.respond("❌ **INCORRECT PIN!** Wipe canceled.", buttons=get_main_keyboard(chat_id))
                user_states[chat_id] = None
                return
                
            wipe_type = state.get("wipe_type")
            await event.respond(f"✅ **PIN Verified!** Executing wipe: {wipe_type}...\n*(Please wait, this will be handled by the background engine shortly.)*", buttons=get_main_keyboard(chat_id))
            
            # Queue the wipe command for the forwarder engine
            user_data["pending_wipe"] = wipe_type
            save_user_data(chat_id, user_data)
            user_states[chat_id] = None
            return

        elif step == "waiting_for_manual_session":
            try: await event.message.delete()
            except: pass
            await event.respond("⏳ Testing your session string, please wait...")
            try:
                user_data = get_user_data(chat_id)
                # Use standard Telegram Android API ID for testing the session
                tmp_client = TelegramClient(StringSession(text), 6, "eb06d4abfb49dc3eeb1aeb98ae0f581e")
                await tmp_client.connect()
                if await tmp_client.is_user_authorized():
                    user_data["session_string"] = text
                    user_data["api_id"] = 6
                    user_data["api_hash"] = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
                    save_user_data(chat_id, user_data)
                    user_states[chat_id] = None
                    await tmp_client.disconnect()
                    await event.respond("✅ **Session Successfully Connected!**", buttons=get_main_keyboard(chat_id))
                    
                else:
                    await tmp_client.disconnect()
                    await event.respond("❌ Invalid session string (Not authorized).", buttons=[[Button.inline("🔙 Cancel", b"back")]])
            except Exception as e:
                await event.respond(f"❌ Failed to connect session: {e}", buttons=[[Button.inline("🔙 Cancel", b"back")]])
            return
        
        elif step == "waiting_for_api_id":
            if not text.isdigit():
                await event.respond("❌ `API_ID` must be numbers only. Try again.")
                return
            state["api_id"] = int(text)
            state["step"] = "waiting_for_api_hash"
            await event.respond("Great. Now reply with your `API_HASH` (the long random string).", buttons=[[Button.inline("🔙 Cancel", b"back")]])
            return
            
        elif step == "waiting_for_api_hash":
            state["api_hash"] = text
            state["step"] = "waiting_for_login_method"
            await event.respond(
                "Great! How would you like to connect your account?\n\n"
                "📱 **QR Code (Recommended):** Bypass SMS limits instantly.\n"
                "✉️ **Phone Number:** Standard SMS login.", 
                buttons=[
                    [Button.inline("📱 QR Code Login", b"login_qr")],
                    [Button.inline("✉️ Phone Number", b"login_phone")],
                    [Button.inline("🔙 Cancel", b"back")]
                ]
            )
            return
            
        elif step == "waiting_for_phone":
            try: await event.message.delete()
            except: pass
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
                
                # Determine where the code went
                delivery_method = str(type(res.type).__name__)
                where = "your Telegram App (Official 'Telegram' Service Account)"
                if "Sms" in delivery_method:
                    where = "an SMS text message"
                elif "Call" in delivery_method:
                    where = "a Phone Call"
                    
                await event.respond(
                    f"📬 **Telegram has sent your login code!**\n\n"
                    f"**Number used:** `{state['phone']}`\n"
                    f"**Delivery Method:** {where} (`{delivery_method}`)\n\n"
                    "⚠️ **CRITICAL INSTRUCTION:** Telegram's security system will instantly block the login if you just send the code normally.\n\n"
                    "👉 **You MUST put spaces between the numbers.**\n"
                    "For example, if your code is `12345`, you must reply with:\n`1 2 3 4 5`\n\n"
                    "*(The bot will automatically remove the spaces for you and delete the message for security)*", 
                    buttons=[
                        [Button.inline("🔁 Resend Code", b"resend_code")],
                        [Button.inline("🔙 Cancel", b"back")]
                    ]
                )
            except Exception as e:
                await event.respond(f"❌ Failed to request code: {e}")
                await tmp_client.disconnect()
                user_states[chat_id] = None
            return
            
        elif step == "waiting_for_code":
            try: await event.message.delete()
            except: pass
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
                user_data = get_user_data(chat_id)
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
            try: await event.message.delete()
            except: pass
            session_data = login_sessions.get(chat_id)
            if not session_data:
                return
            tmp_client = session_data["client"]
            password = text
            try:
                await tmp_client.sign_in(password=password)
                session_string = tmp_client.session.save()
                await tmp_client.disconnect()
                  
                if "msg_id" in session_data:
                    try:
                        await bot.delete_messages(chat_id, session_data["msg_id"])
                    except:
                        pass
                        
                del login_sessions[chat_id]
                
                user_data = get_user_data(chat_id)
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
            new_items = []
            import re
            for x in text.split(','):
                x = x.strip()
                if not x: continue
                if "t.me/c/" in x:
                    match = re.search(r't\.me/c/(\d+)', x)
                    if match:
                        new_items.append(f"-100{match.group(1)}")
                        continue
                elif "t.me/" in x:
                    match = re.search(r't\.me/([^/\?]+)', x)
                    if match:
                        username = match.group(1)
                        if username not in ["c", "joinchat", "+"]:
                            new_items.append(f"@{username}")
                            continue
                new_items.append(x)
        if not new_items:
            await event.respond("❌ I couldn't detect a valid ID. Please forward a message from the channel, or type the ID manually.")
            return
            
        added = []
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
            res_msg += f"✅ Added: {', '.join(added)}\n"
        if removed:
            res_msg += f"🗑️ Removed: {', '.join(removed)}\n"
            
        await event.respond(res_msg.strip() or "No changes made.", buttons=get_main_keyboard(chat_id))
        
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
        elif text.startswith("EXCLUDE="):
            user_data["exclude_link_keywords"] = text.split("=", 1)[1].strip()
            save_user_data(chat_id, user_data)
            user_states[chat_id] = None
            await event.respond("✅ Link exclusions updated!", buttons=get_main_keyboard(chat_id))
        elif text.upper() == "CLEAR EXCLUDE":
            user_data["exclude_link_keywords"] = ""
            save_user_data(chat_id, user_data)
            user_states[chat_id] = None
            await event.respond("✅ Link exclusions cleared!", buttons=get_main_keyboard(chat_id))
        else:
            await event.respond("❌ Invalid format. Use `LINK=...`, `USER=...` or `EXCLUDE=...`")
            
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
    elif state == "waiting_for_pro_id" and is_admin(chat_id):
        target_uid = text.strip()
        if not target_uid.lstrip('-').isdigit():
            await event.respond("❌ Invalid ID. It must be a number.", buttons=get_main_keyboard(chat_id))
            user_states[chat_id] = None
            return
            
        target_uid = int(target_uid)
        t_data = get_user_data(target_uid)
        
        # Toggle PRO status
        current_pro = t_data.get("is_pro", False)
        t_data["is_pro"] = not current_pro
        
        # Save
        from database_manager import save_user_data
        save_user_data(target_uid, t_data)
        
        status = "✅ GRANTED" if t_data["is_pro"] else "❌ REVOKED"
        await event.respond(f"💎 PRO status for user `{target_uid}` is now {status}.", buttons=get_main_keyboard(chat_id))
        user_states[chat_id] = None
        return

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
@bot.on(events.NewMessage(pattern='/admin_logs'))
async def admin_logs_handler(event):
    chat_id = event.chat_id
    if not is_admin(chat_id):
        return
        
    try:
        with open('forwarder.log', 'r', encoding='utf-8') as log_file:
            logs = log_file.readlines()[-30:]
            log_text = "".join(logs)
            if not log_text:
                await event.respond("Logs are empty.")
            else:
                await event.respond(f"**Latest Logs:**\n{log_text[-3500:]}")
    except Exception as e:
        await event.respond(f"Failed to read logs: {e}")

bot.run_until_disconnected()
