import os
import asyncio
import sys

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("forwarder.log", "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger()
sys.stderr = sys.stdout
import re
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaWebPage
from telethon.sessions import StringSession
from telethon.errors import (
    AuthKeyUnregisteredError, AuthKeyInvalidError,
    SessionRevokedError, SessionExpiredError, UserDeactivatedBanError
)

from database_manager import get_all_users, get_user_data, save_message_map

active_clients = {}
ai_semaphore = asyncio.Semaphore(2)  # Limit concurrent AI processing to prevent memory spikes on Render (512MB RAM limit)

import datetime
import time

def is_in_sleep_mode(user_data):
    sleep_mode = user_data.get("sleep_mode", {})
    if not sleep_mode.get("enabled"): return False
    
    offset = float(sleep_mode.get("timezone_offset", 0))
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=offset)
    current_time = now.strftime("%H:%M")
    
    start = sleep_mode.get("start_time", "22:00")
    end = sleep_mode.get("end_time", "08:00")
    
    if start < end:
        return start <= current_time <= end
    else:
        return current_time >= start or current_time <= end

def apply_rules(text, user_data):
    if not text:
        return text
    
    # 1. Text Swaps
    swaps = user_data.get("text_swaps", {})
    for old_w, new_w in swaps.items():
        if old_w and new_w:
            text = re.sub(re.escape(old_w), new_w, text, flags=re.IGNORECASE)
            
    # 2. Replace Links
    link_replacement = user_data.get("replace_all_links_with", "").strip()
    if link_replacement:
        # Match http/https, www, domain.com/path, and common domains without protocol
        url_pattern = r'(?i)(?:https?://|www\.)[^\s]+|\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}/[^\s]*|\b(?:t\.me|telegram\.me|youtube\.com|youtu\.be|instagram\.com|twitter\.com|x\.com|facebook\.com|tiktok\.com|bit\.ly)[^\s]*'
        
        def link_replacer(match):
            matched_str = match.group(0)
            # If the original link did NOT have http/https, we remove it from the replacement link too!
            if not matched_str.lower().startswith('http'):
                return re.sub(r'^https?://', '', link_replacement, flags=re.IGNORECASE)
            return link_replacement
            
        text = re.sub(url_pattern, link_replacer, text)

    # 3. Replace Usernames
    user_replacement = user_data.get("replace_all_usernames_with", "").strip()
    if user_replacement:
        username_pattern = r'@[\w_]+'
        text = re.sub(username_pattern, user_replacement, text)
        
    # 4. Strip Account/Payment Details (Crypto & Banks)
    if user_data.get("strip_payment_details", False):
        import re
        # ETH/BSC
        text = re.sub(r'(?i)^.*0x[a-f0-9]{40}.*$\n?', '', text, flags=re.MULTILINE)
        # BTC (Legacy, Segwit)
        text = re.sub(r'(?i)^.*(?<![a-z0-9])(1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})(?![a-z0-9]).*$\n?', '', text, flags=re.MULTILINE)
        # TRON/USDT TRC20 (Starts with T, 34 chars)
        text = re.sub(r'(?i)^.*(?<![a-z0-9])T[a-km-zA-HJ-NP-Z1-9]{33}(?![a-z0-9]).*$\n?', '', text, flags=re.MULTILINE)
        # Bank/Account keywords
        text = re.sub(r'(?i)^.*(account\s*details|account\s*name|account\s*no|acc\s*no|account\s*number|bank\s*:|bank\s*name|bank\s*account|routing|iban|sort\s*code|paypal|cashapp|skrill|neteller|paystack|opay|palmpay|kuda|moniepoint).*$\n?', '', text, flags=re.MULTILINE)

    return text



async def ai_process_image(client, message, chat_id, user_data):
    mode = user_data.get("ai_watermark_mode", "off")
    target = user_data.get("ai_watermark_target", "")
    
    if mode == "off" or not target:
        return message.media
        
    import os
    import ast
    import re
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    from google import genai
    from dotenv import load_dotenv
    
    load_dotenv('.env')
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("No GEMINI_API_KEY found, skipping AI watermark.")
        return message.media
        
    try:
        # Download media
        print(f"[Tenant {chat_id}] Downloading image for AI watermark processing...")
        temp_path = await client.download_media(message, file=f"temp_{message.id}_{chat_id}.png")
        if not temp_path:
            return message.media
            
        img = Image.open(temp_path).convert("RGB")
        width, height = img.size
        
        genai_client = genai.Client(api_key=api_key)
        prompt = f"Find the exact bounding box for the text block '{target}'. Return the coordinates as a JSON array [ymin, xmin, ymax, xmax] normalized to 1000 (where ymin is top, xmin is left, ymax is bottom, xmax is right). For horizontal text, xmax-xmin is usually much larger than ymax-ymin."
        
        import asyncio
        response = await asyncio.to_thread(
            genai_client.models.generate_content,
            model='gemini-3.5-flash',
            contents=[img, prompt],
            config={
                "response_mime_type": "application/json"
            }
        )
        
        try:
            import json
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                # Strip ```json and ```
                raw_text = raw_text.strip("`").removeprefix("json").strip()
                
            box = json.loads(raw_text)
            
            # Handle list of dicts: [{"box_2d": [ymin, xmin, ymax, xmax]}]
            if isinstance(box, list) and len(box) > 0 and isinstance(box[0], dict) and "box_2d" in box[0]:
                box = box[0]["box_2d"]
                
            # Sometimes Gemini swaps coordinates if confused, let's enforce ymin < ymax and xmin < xmax
            # And if height > width (vertical stripe), swap them back!
            if isinstance(box, list) and len(box) == 4:
                # box is [a, b, c, d]. We expect [ymin, xmin, ymax, xmax]
                # To be completely safe:
                # The text is horizontal, so width (x) > height (y)
                val1, val2, val3, val4 = box
                
                # Sort values to find the actual dimensions
                # If val3 - val1 (height) > val4 - val2 (width), it likely swapped x and y.
                if (val3 - val1) > (val4 - val2):
                    ymin, xmin, ymax, xmax = val2, val1, val4, val3
                else:
                    ymin, xmin, ymax, xmax = val1, val2, val3, val4
                    
                ymin, ymax = min(ymin, ymax), max(ymin, ymax)
                xmin, xmax = min(xmin, xmax), max(xmin, xmax)
            else:
                print(f"[Tenant {chat_id}] Invalid box format from Gemini: {box}")
                try:
                    await client.send_message(message.chat_id, f"❌ AI Error: Could not find the exact text block in the image.")
                except:
                    pass
                return message.media
                
                # Now we know ymin, xmin, ymax, xmax are correct!
            
            top = int(ymin * height / 1000)
            left = int(xmin * width / 1000)
            bottom = int(ymax * height / 1000)
            right = int(xmax * width / 1000)
            
            # Add extra generous padding to catch hallucinated coordinates
            padding = 15
            left = max(0, left - padding)
            top = max(0, top - padding)
            right = min(width, right + padding)
            bottom = min(height, bottom + padding)
            
            if mode == "remove" or mode == "replace":
                # Sample the background color from the edge to completely paint over the old text
                sample_color = img.getpixel((max(0, left-2), max(0, top-2)))
                draw = ImageDraw.Draw(img)
                draw.rectangle([left, top, right, bottom], fill=sample_color)
                
            if mode == "replace":
                replacement_text = user_data.get("ai_watermark_replace", "")
                
                # Try to pick a solid background color from the edge of the box
                sample_color = img.getpixel((max(0, left-2), max(0, top-2)))
                
                draw = ImageDraw.Draw(img)
                draw.rectangle([left, top, right, bottom], fill=sample_color)
                
                if replacement_text:
                    # Draw text in the middle
                    # We just use default font as it scales better than nothing
                    # Or try loading a truetype if available
                    font = None
                    try:
                        font = ImageFont.truetype("arial.ttf", size=int((bottom-top)*0.6))
                    except:
                        font = ImageFont.load_default()
                        
                    # Calculate center
                    text_x = left + (right - left) // 2
                    text_y = top + (bottom - top) // 2
                    
                    # Ensure text is visible (white on dark, black on light)
                    brightness = sum(sample_color) / 3
                    text_color = (0,0,0) if brightness > 128 else (255,255,255)
                    
                    draw.text((text_x, text_y), replacement_text, fill=text_color, font=font, anchor="mm")
        except Exception as ex:
            print(f"[Tenant {chat_id}] Failed to parse Gemini response: {ex}")
            if 'img' in locals(): img.close()
            return message.media
                    
        out_path = f"processed_{message.id}_{chat_id}.png"
        img.save(out_path)
        img.close()
        
        # Cleanup temp
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        print(f"[Tenant {chat_id}] AI Watermark processing complete.")
        return out_path
        
    except Exception as e:
        print(f"[Tenant {chat_id}] AI Watermark error: {e}")
        if 'img' in locals(): img.close()
        return message.media


async def execute_forward(message, chat_id, user_data):
    import os
    from database_manager import save_user_data
    target_channels = user_data.get('targets', [])
    
    modified_text = apply_rules(message.text, user_data)
    media_to_send = message.media
    
    client = active_clients.get(chat_id)
    if not client: return

    if message.media:
        is_enabled = user_data.get("image_override_enabled", True)
        if is_enabled and (user_data.get("image_swap_path", "").strip() or user_data.get("image_swap_url", "").strip()):
            image_swap_path = user_data.get("image_swap_path", "").strip()
            image_swap_url = user_data.get("image_swap_url", "").strip()
            
            if image_swap_path and os.path.exists(image_swap_path):
                media_to_send = image_swap_path
            elif image_swap_url:
                media_to_send = image_swap_url
        else:
            # If standard image override is OFF, process AI watermark if enabled
            mode = user_data.get("ai_watermark_mode", "off")
            if mode != "off":
                media_to_send = await ai_process_image(client, message, chat_id, user_data)
    
    smart_delay = user_data.get("smart_delay_enabled", False)
    if smart_delay:
        import random
        import asyncio
        delay_seconds = random.randint(60, 180)
        print(f"[Tenant {chat_id}] Smart Delay: Waiting {delay_seconds} seconds before forwarding...")
        await asyncio.sleep(delay_seconds)
        
    try:
        success = False
        for target in target_channels:
            try:
                t = int(target)
            except ValueError:
                t = target
                
            try:
                sent = None
                if media_to_send and not isinstance(media_to_send, MessageMediaWebPage):
                    if media_to_send == message.media:
                        # Passing the original message object guarantees Telegram resolves the media access hash
                        sent = await client.send_message(t, modified_text, file=message)
                    else:
                        # Sending a local file or URL override
                        sent = await client.send_file(t, media_to_send, caption=modified_text)
                else:
                    if modified_text:
                        sent = await client.send_message(t, modified_text, link_preview=True)
                
                # SAVE MAPPING FOR MIRROR DELETION
                if sent and getattr(sent, 'id', None):
                    if isinstance(message, list):
                        src_id = message[0].id
                    else:
                        src_id = message.id
                    save_message_map(chat_id, message.chat_id, src_id, target, sent.id)
                success = True
            except Exception as e:
                print(f"[Tenant {chat_id}] Failed to forward cleanly to {t}: {e}")
                try:
                    await client.send_message(chat_id, f"⚠️ **DEBUG: Failed to send media to {t}**\nError: `{e}`")
                except:
                    pass
                # Try fallback just for this target
                if modified_text:
                    try:
                        sent = await client.send_message(t, modified_text)
                        if sent and getattr(sent, 'id', None):
                            if isinstance(message, list):
                                src_id = message[0].id
                            else:
                                src_id = message.id
                            save_message_map(chat_id, message.chat_id, src_id, target, sent.id)
                        success = True
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
    finally:
        # Cleanup AI processed images
        if isinstance(media_to_send, str) and media_to_send.startswith("processed_") and os.path.exists(media_to_send):
            try:
                os.remove(media_to_send)
            except:
                pass


async def handle_message(event, chat_id):
    print(f"[DEBUG-ALL-MESSAGES] Tenant {chat_id} received message from {event.chat_id}")
    from database_manager import save_user_data
    user_data = get_user_data(chat_id)
    
    source_channels = user_data.get('sources', [])
    target_channels = user_data.get('targets', [])
    
    if not source_channels or not target_channels:
        return

    is_source = False
    incoming_str = str(event.chat_id)
    # Build all possible representations of the incoming channel ID
    incoming_variants = {incoming_str}
    if incoming_str.startswith('-100'):
        incoming_variants.add(incoming_str[4:])   # bare digits without -100
        incoming_variants.add(incoming_str[1:])   # without leading dash
    elif incoming_str.lstrip('-').isdigit():
        incoming_variants.add(f"-100{incoming_str.lstrip('-')}")  # add -100 prefix

    for src in source_channels:
        src_str = str(src).strip()
        # Numeric match against all variants
        if src_str in incoming_variants or src_str.lstrip('-') in {v.lstrip('-') for v in incoming_variants}:
            is_source = True
            print(f"[MATCH-ID] {src_str} matched {incoming_str}")
            break
        # Username match
        if src_str.startswith('@') or not any(ch.isdigit() for ch in src_str):
            if hasattr(event, 'chat') and event.chat and getattr(event.chat, 'username', None):
                uname = event.chat.username
                if src_str == f'@{uname}' or src_str == uname:
                    is_source = True
                    print(f"[MATCH-USERNAME] {src_str}")
                    break
        # Debug unmatched numeric sources
        if any(ch.isdigit() for ch in src_str) and not src_str.startswith('@'):
            src_digits = src_str.lstrip('-').lstrip('100')
            in_digits = incoming_str.lstrip('-').lstrip('100')
            print(f"[DEBUG-MATCH] incoming={incoming_str} ({in_digits}) vs saved={src_str} ({src_digits})")
            
    if not is_source:
        return
        
    print(f"[Tenant {chat_id}] Received message from source: {event.chat_id}")
    
    drip_interval = user_data.get("drip_interval", 0)
    in_sleep = is_in_sleep_mode(user_data)
    
    if drip_interval > 0 or in_sleep:
        queue = user_data.get("drip_queue", [])
        preview = event.message.text[:50] + "..." if event.message.text else "[Media/No Text]"
        queue.append({
            "msg_id": event.message.id, 
            "source_chat_id": event.chat_id,
            "preview": preview,
            "added_at": time.time()
        })
        user_data["drip_queue"] = queue
        save_user_data(chat_id, user_data)
        reason = "Sleep Mode" if in_sleep else "Drip Posting"
        print(f"[Tenant {chat_id}] Message queued for {reason}. (Queue size: {len(queue)})")
        return
        
    await execute_forward(event.message, chat_id, user_data)

async def monitor_users():
    print("Starting Multi-Tenant Forwarding Engine...")
    while True:
        try:
            # 1. Write the main heartbeat so the bot knows the engine is alive
            import time, json
            with open('status.json', 'w') as f:
                json.dump({"last_seen": time.time(), "status": "online"}, f)
                
            # 2. Check all tenants
            all_users = get_all_users()
            
            import time
            from database_manager import save_user_data
                        # Process Drip Queues
            for chat_id, client in list(active_clients.items()):
                udata = get_user_data(chat_id)
                interval = udata.get("drip_interval", 0)
                queue = udata.get("drip_queue", [])
                
                if queue and not is_in_sleep_mode(udata):
                    last_drip = udata.get("last_drip_time", 0)
                    
                    # interval is stored in seconds directly
                    eff_interval = interval if interval > 0 else 2
                    
                    if time.time() - last_drip >= eff_interval:
                        item = queue.pop(0)
                        udata["last_drip_time"] = time.time()
                        udata["drip_queue"] = queue
                        save_user_data(chat_id, udata)
                        
                        print(f"[Tenant {chat_id}] Popping queued message {item['msg_id']}...")
                        try:
                            msgs = await client.get_messages(item["source_chat_id"], ids=item["msg_id"])
                            if msgs:
                                asyncio.create_task(execute_forward(msgs, chat_id, udata))
                        except Exception as e:
                            print(f"[Tenant {chat_id}] Failed to fetch queued message: {e}")

                # --- Process Pending Manual Wipes ---
                pending_wipe = udata.get("pending_wipe")
                if pending_wipe:
                    print(f"[Tenant {chat_id}] Executing wipe: {pending_wipe}")
                    targets = udata.get("targets", [])
                    for t in targets:
                        try:
                            tc = int(t) if str(t).lstrip("-").isdigit() else t
                            if pending_wipe == "10":
                                msgs_list = await client.get_messages(tc, limit=10)
                                if msgs_list:
                                    await client.delete_messages(tc, [m.id for m in msgs_list])
                            elif pending_wipe == "50":
                                msgs_list = await client.get_messages(tc, limit=50)
                                if msgs_list:
                                    await client.delete_messages(tc, [m.id for m in msgs_list])
                            elif pending_wipe == "today":
                                import datetime
                                today_start = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                                ids_to_del = []
                                async for msg in client.iter_messages(tc):
                                    if msg.date and msg.date >= today_start:
                                        ids_to_del.append(msg.id)
                                    else:
                                        break
                                for i in range(0, len(ids_to_del), 100):
                                    await client.delete_messages(tc, ids_to_del[i:i+100])
                            print(f"[Tenant {chat_id}] Wipe '{pending_wipe}' done for {tc}")
                        except Exception as e:
                            print(f"[Tenant {chat_id}] Wipe failed for {t}: {e}")
                    udata["pending_wipe"] = None
                    save_user_data(chat_id, udata)

                # --- Process Auto-Delete Rolling Window ---
                auto_limit = udata.get("auto_delete_limit", 0)
                if auto_limit > 0:
                    last_clean = udata.get("last_auto_clean", 0)
                    if time.time() - last_clean > 300:
                        targets = udata.get("targets", [])
                        for t in targets:
                            try:
                                tc = int(t) if str(t).lstrip("-").isdigit() else t
                                ids_to_del = []
                                count = 0
                                async for msg in client.iter_messages(tc):
                                    count += 1
                                    if count > auto_limit:
                                        ids_to_del.append(msg.id)
                                for i in range(0, len(ids_to_del), 100):
                                    await client.delete_messages(tc, ids_to_del[i:i+100])
                                if ids_to_del:
                                    print(f"[Tenant {chat_id}] Auto-deleted {len(ids_to_del)} old msgs in {tc}")
                            except Exception as e:
                                print(f"[Tenant {chat_id}] Auto-delete failed for {t}: {e}")
                        udata["last_auto_clean"] = time.time()
                        save_user_data(chat_id, udata)

            # Start new clients
            for chat_id in all_users:
                user_data = get_user_data(chat_id)
                session_str = user_data.get("session_string", "")
                
                if session_str and chat_id not in active_clients:
                    print(f"Booting Engine for Tenant {chat_id}...")
                    try:
                        api_id = user_data.get("api_id")
                        api_hash = user_data.get("api_hash")
                        client = TelegramClient(StringSession(session_str), api_id, api_hash)
                        await client.connect()
                        
                        # Populate entity cache to make -100 IDs work for both sources and targets
                        try:
                            print(f"[Tenant {chat_id}] Fetching dialogs to populate entity cache...")
                            await client.get_dialogs(limit=300)
                        except Exception as e:
                            print(f"[Tenant {chat_id}] Failed to fetch dialogs: {e}")
                            
                        # CRITICAL: Properly remove ALL existing handlers to prevent stacking
                        for cb, ev in list(client.list_event_handlers()):
                            client.remove_event_handler(cb, ev)
                        # incoming=True means ONLY messages received, NOT messages sent by this account
                        client.add_event_handler(
                            lambda e, cid=chat_id: handle_message(e, cid),
                            events.NewMessage(incoming=True)
                        )
                        active_clients[chat_id] = client
                        print(f"✅ Engine ONLINE for Tenant {chat_id}")
                    except (AuthKeyUnregisteredError, AuthKeyInvalidError,
                            SessionRevokedError, SessionExpiredError, UserDeactivatedBanError) as e:
                        # Session was killed externally - clean up and notify tenant
                        print(f"[Tenant {chat_id}] ⚠️ SESSION REVOKED: {e}. Clearing session.")
                        try: await client.disconnect()
                        except: pass
                        user_data["session_string"] = ""
                        user_data["is_active"] = False
                        from database_manager import save_user_data
                        save_user_data(chat_id, user_data)
                        active_clients.pop(chat_id, None)
                        # Notify tenant
                        try:
                            BOT_TOKEN = os.getenv("BOT_TOKEN")
                            import aiohttp
                            msg = (
                                "⚠️ *Account Disconnected!*\n\n"
                                "Your Telegram session was logged out or revoked from outside the bot "
                                "(e.g. you logged out on your phone or Telegram revoked your session).\n\n"
                                "Your forwarding engine has been stopped automatically.\n\n"
                                "👉 Please open the bot and reconnect your account to resume forwarding."
                            )
                            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                            async with aiohttp.ClientSession() as sess:
                                await sess.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
                        except Exception as notify_err:
                            print(f"[Tenant {chat_id}] Failed to notify: {notify_err}")
                    except Exception as e:
                        # Check if it's an auth/session error (covers revoke, invalid, corrupt session)
                        err_str = str(type(e).__name__).lower() + str(e).lower()
                        is_session_error = any(x in err_str for x in [
                            "authkey", "session", "revoked", "expired", "deactivated",
                            "banned", "unregistered", "invalid", "struct", "unpack"
                        ])
                        if is_session_error:
                            print(f"[Tenant {chat_id}] ⚠️ SESSION ERROR on boot: {type(e).__name__}: {e}. Clearing.")
                            try: await client.disconnect()
                            except: pass
                            user_data["session_string"] = ""
                            user_data["is_active"] = False
                            from database_manager import save_user_data
                            save_user_data(chat_id, user_data)
                            active_clients.pop(chat_id, None)
                            try:
                                BOT_TOKEN = os.getenv("BOT_TOKEN")
                                import aiohttp
                                msg = (
                                    "⚠️ *Account Disconnected!*\n\n"
                                    "Your Telegram session was logged out or revoked from outside the bot "
                                    "(e.g. you logged out on your phone or Telegram revoked your session).\n\n"
                                    "Your forwarding engine has been stopped automatically.\n\n"
                                    "👉 Please open the bot and reconnect your account to resume forwarding."
                                )
                                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                                async with aiohttp.ClientSession() as sess:
                                    await sess.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
                                print(f"[Tenant {chat_id}] Notified about session error.")
                            except Exception as notify_err:
                                print(f"[Tenant {chat_id}] Failed to notify: {notify_err}")
                        else:
                            print(f"❌ Failed to boot engine for {chat_id}: {type(e).__name__}: {e}")

            # Stop disconnected clients + Health check for revoked sessions
            for chat_id in list(active_clients.keys()):
                client = active_clients[chat_id]
                user_data = get_user_data(chat_id)

                # Proactive ping every 60 seconds — catches revoked sessions
                # even when TCP connection still appears open
                last_ping = getattr(client, '_last_ping', 0)
                if time.time() - last_ping > 60:
                    client._last_ping = time.time()
                    try:
                        await client.get_me()
                    except (AuthKeyUnregisteredError, AuthKeyInvalidError,
                            SessionRevokedError, SessionExpiredError, UserDeactivatedBanError) as e:
                        print(f"[Tenant {chat_id}] ⚠️ SESSION DEAD (ping): {e}")
                        try: await client.disconnect()
                        except: pass
                        user_data["session_string"] = ""
                        user_data["is_active"] = False
                        from database_manager import save_user_data
                        save_user_data(chat_id, user_data)
                        active_clients.pop(chat_id, None)
                        try:
                            BOT_TOKEN = os.getenv("BOT_TOKEN")
                            import aiohttp
                            msg = (
                                "⚠️ *Account Disconnected!*\n\n"
                                "Your Telegram session was logged out or revoked from outside the bot "
                                "(e.g. you logged out on your phone or Telegram revoked your session).\n\n"
                                "Your forwarding engine has been stopped automatically.\n\n"
                                "👉 Please open the bot and reconnect your account to resume forwarding."
                            )
                            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                            async with aiohttp.ClientSession() as sess:
                                await sess.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
                            print(f"[Tenant {chat_id}] Notified about session revoke.")
                        except Exception as notify_err:
                            print(f"[Tenant {chat_id}] Failed to notify: {notify_err}")
                        continue
                    except Exception:
                        pass  # Other ping errors (network etc) are non-fatal

                if not user_data.get("session_string"):
                    print(f"Shutting down Engine for Tenant {chat_id}...")
                    client = active_clients.pop(chat_id)
                    await client.disconnect()

        except Exception as e:
            print(f"Error in monitor loop: {e}")

        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(monitor_users())




