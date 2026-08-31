import os
import asyncio
import re
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaWebPage
from telethon.sessions import StringSession

from database_manager import get_all_users, get_user_data

active_clients = {}

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
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text = re.sub(url_pattern, link_replacement, text)

    # 3. Replace Usernames
    user_replacement = user_data.get("replace_all_usernames_with", "").strip()
    if user_replacement:
        username_pattern = r'@[\w_]+'
        text = re.sub(username_pattern, user_replacement, text)
        
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
            try:
                await client.send_message(message.chat_id, f"❌ AI Error: Could not find the text in the image.")
            except:
                pass
            return message.media
                    
        out_path = f"processed_{message.id}_{chat_id}.png"
        img.save(out_path)
        
        # Cleanup temp
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        print(f"[Tenant {chat_id}] AI Watermark processing complete.")
        return out_path
        
    except Exception as e:
        print(f"[Tenant {chat_id}] AI Watermark error: {e}")
        try:
            await client.send_message(message.chat_id, f"❌ API Error: {e}")
        except:
            pass
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
                status_msg = None
                try:
                    # Send a temporary status message to the source chat so the user knows it's working
                    status_msg = await client.send_message(message.chat_id, "🤖 *AI is cleaning watermark from image...*", reply_to=message.id)
                except Exception:
                    pass
                    
                media_to_send = await ai_process_image(client, message, chat_id, user_data)
                
                if status_msg:
                    try:
                        await status_msg.delete()
                    except Exception:
                        pass
    
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
                if media_to_send and not isinstance(media_to_send, MessageMediaWebPage):
                    await client.send_file(t, media_to_send, caption=modified_text)
                else:
                    if modified_text:
                        await client.send_message(t, modified_text, link_preview=True)
                success = True
            except Exception as e:
                print(f"[Tenant {chat_id}] Failed to forward cleanly to {t}: {e}")
                # Try fallback just for this target
                if modified_text:
                    try:
                        await client.send_message(t, modified_text)
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
    from database_manager import save_user_data
    user_data = get_user_data(chat_id)
    
    source_channels = user_data.get('sources', [])
    target_channels = user_data.get('targets', [])
    
    if not source_channels or not target_channels:
        return

    is_source = False
    
    incoming_id_clean = str(event.chat_id).replace("-100", "").replace("-", "")
    for src in source_channels:
        if str(src).startswith("@") or not any(char.isdigit() for char in str(src)):
            continue
        src_clean = str(src).replace("-100", "").replace("-", "")
        if src_clean == incoming_id_clean:
            is_source = True
            break
            
    if not is_source and str(event.chat_id) in source_channels:
        is_source = True
        
    if not is_source and hasattr(event, 'chat') and event.chat and hasattr(event.chat, 'username') and event.chat.username:
        if f"@{event.chat.username}" in source_channels or event.chat.username in source_channels:
            is_source = True
            
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
                    
                    # If interval is 0, we are just waking up from sleep mode, flush 1 message quickly (e.g. every 2 secs)
                    eff_interval = interval * 60 if interval > 0 else 2
                    
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
                        
                        # Use a lambda or partial to pass the chat_id into the event handler
                        client.add_event_handler(lambda e, cid=chat_id: handle_message(e, cid), events.NewMessage)
                        active_clients[chat_id] = client
                        print(f"✅ Engine ONLINE for Tenant {chat_id}")
                    except Exception as e:
                        print(f"❌ Failed to boot engine for {chat_id}: {e}")

            # Stop disconnected clients
            for chat_id in list(active_clients.keys()):
                user_data = get_user_data(chat_id)
                if not user_data.get("session_string"):
                    print(f"Shutting down Engine for Tenant {chat_id}...")
                    client = active_clients.pop(chat_id)
                    await client.disconnect()

        except Exception as e:
            print(f"Error in monitor loop: {e}")
            
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(monitor_users())




