import os
import sys
import time
import datetime
import json
import re
import random
import asyncio

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

media_cache_memory = {}

def trim_memory():
    import gc
    gc.collect()
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("forwarder.log", "a", encoding="utf-8")

    def write(self, message):
        try:
            self.terminal.write(message)
        except Exception:
            try:
                enc = getattr(self.terminal, 'encoding', None) or 'utf-8'
                safe_msg = message.encode(enc, errors='replace').decode(enc)
                self.terminal.write(safe_msg)
            except Exception:
                pass
        try:
            self.log.write(message)
            self.log.flush()
        except Exception:
            pass

    def flush(self):
        try:
            self.terminal.flush()
        except Exception:
            pass
        try:
            self.log.flush()
        except Exception:
            pass

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

from database_manager import get_all_users, get_user_data, save_user_data, save_message_map, get_feature_toggles

active_clients = {}
tenant_cooldowns = {}
processed_messages_cache = {}

def get_canonical_id(peer):
    if peer is None:
        return ""
    try:
        from telethon import utils
        pid = utils.get_peer_id(peer)
        s = str(pid).strip()
        if s.startswith("-100"):
            return s[4:]
        return s.lstrip("-")
    except Exception:
        pass
    s = str(getattr(peer, 'id', peer)).strip()
    if s.startswith("-100"):
        return s[4:]
    if s.startswith("100") and len(s) > 10:
        return s[3:]
    return s.lstrip("-").lower().lstrip("@")

def is_duplicate_message(chat_id, source_chat_id, msg_id):
    now = time.time()
    if len(processed_messages_cache) > 3000:
        to_del = [k for k, ts in list(processed_messages_cache.items()) if now - ts > 300]
        for k in to_del:
            processed_messages_cache.pop(k, None)

    src_canon = get_canonical_id(source_chat_id)
    key = (str(chat_id), src_canon, str(msg_id))
    if key in processed_messages_cache:
        if now - processed_messages_cache[key] < 180:
            return True
    processed_messages_cache[key] = now
    return False

db_semaphore = asyncio.Semaphore(10)
restricted_download_semaphore = asyncio.Semaphore(1)  # Prevent mass OOM from concurrent restricted downloads
forward_semaphore = asyncio.Semaphore(15)  # Limit concurrent message processing to prevent OOM on massive channel dumps

import datetime
import time

def is_pro(chat_id):
    import os
    if str(chat_id) == str(os.getenv("ADMIN_ID", "")).strip(): return True
    return get_user_data(chat_id).get("is_pro", False)

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
    import re
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
        url_pattern = r'(?i)(?:https?://|www\.)(?!(?:t\.me|telegram\.me))[^\s]+|\b(?!(?:t\.me|telegram\.me))[a-zA-Z0-9.-]+\.(?:com|net|org|io|co|me|gl|ly|tv|ai|app|dev|link|click|site|xyz|bet|casino|game|vip|pro|top|club|online)(?:/[^\s]*)?\b|\b(?:youtube\.com|youtu\.be|instagram\.com|twitter\.com|x\.com|facebook\.com|tiktok\.com|bit\.ly)[^\s]*'
        
        exclude_keywords = [k.strip().lower() for k in user_data.get("exclude_link_keywords", "").split(",") if k.strip()]
        
        def link_replacer(match):
            matched_str = match.group(0)
            
            # Check exclusions
            matched_lower = matched_str.lower()
            for ex in exclude_keywords:
                if ex in matched_lower:
                    return matched_str
                    
            # If the original link did NOT have http/https, we remove it from the replacement link too!
            if not matched_str.lower().startswith('http'):
                return re.sub(r'^https?://', '', link_replacement, flags=re.IGNORECASE)
            return link_replacement
            
        text = re.sub(url_pattern, link_replacer, text)

    # 3. Replace Usernames AND Telegram DM/Group Links
    user_replacement = user_data.get("replace_all_usernames_with", "").strip()
    if user_replacement:
        username_pattern = r'(?i)(?:https?://)?(?:t\.me/|telegram\.me/|@)[\w_]+'
        
        def username_replacer(match):
            matched = match.group(0)
            if 't.me' in matched.lower() or 'telegram.me' in matched.lower():
                if user_replacement.startswith('@'):
                    return f't.me/{user_replacement[1:]}'
                return user_replacement
            return user_replacement
            
        text = re.sub(username_pattern, username_replacer, text)
    # 4. Strip Account/Payment Details (Crypto & Banks)
    if user_data.get("strip_payment_details", False):
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
    if not getattr(message, 'photo', None):
        return message.media

    file_size = getattr(message.file, 'size', 0)
    if file_size > 8 * 1024 * 1024:
        print(f"[Tenant {chat_id}] Photo exceeds 8MB ({file_size} bytes). Forwarding as-is to preserve memory.")
        return message.media

    from dotenv import load_dotenv
    load_dotenv('.env')
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("No GEMINI_API_KEY found, skipping AI watermark.")
        return message.media
        
    temp_path = None
    out_path = None
    img = None
    preview = None
    try:
        print(f"[Tenant {chat_id}] Downloading image for AI watermark processing...")
        temp_path = await client.download_media(message, file=f"temp_{message.id}_{chat_id}.png")
        if not temp_path or not os.path.exists(temp_path):
            return message.media
            
        img = Image.open(temp_path).convert("RGB")
        width, height = img.size
        
        global _shared_genai_client
        if '_shared_genai_client' not in globals() or _shared_genai_client is None:
            _shared_genai_client = genai.Client(api_key=api_key)
        genai_client = _shared_genai_client
        
        prompt = f"Find the exact bounding box for the text block '{target}'. Return the coordinates as a JSON array [ymin, xmin, ymax, xmax] normalized to 1000 (where ymin is top, xmin is left, ymax is bottom, xmax is right). For horizontal text, xmax-xmin is usually much larger than ymax-ymin."
        
        # Downscale a copy to 768px for Gemini text detection to save 95% RAM
        preview = img.copy()
        preview.thumbnail((768, 768), Image.Resampling.LANCZOS)

        import asyncio
        response = await asyncio.to_thread(
            genai_client.models.generate_content,
            model='gemini-2.5-flash',
            contents=[preview, prompt],
            config={
                "response_mime_type": "application/json"
            }
        )
        del preview
        preview = None
        
        try:
            import json
            raw_text = response.text.strip()
            del response
            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`").removeprefix("json").strip()
                
            box = json.loads(raw_text)
            
            if isinstance(box, list) and len(box) > 0 and isinstance(box[0], dict) and "box_2d" in box[0]:
                box = box[0]["box_2d"]
                
            if isinstance(box, list) and len(box) == 4:
                val1, val2, val3, val4 = box
                if (val3 - val1) > (val4 - val2):
                    ymin, xmin, ymax, xmax = val2, val1, val4, val3
                else:
                    ymin, xmin, ymax, xmax = val1, val2, val3, val4
                    
                ymin, ymax = min(ymin, ymax), max(ymin, ymax)
                xmin, xmax = min(xmin, xmax), max(xmin, xmax)
            else:
                print(f"[Tenant {chat_id}] Invalid box format from Gemini: {box}")
                return message.media
            
            top = int(ymin * height / 1000)
            left = int(xmin * width / 1000)
            bottom = int(ymax * height / 1000)
            right = int(xmax * width / 1000)
            
            padding = 15
            left = max(0, left - padding)
            top = max(0, top - padding)
            right = min(width, right + padding)
            bottom = min(height, bottom + padding)
            
            if mode == "remove" or mode == "replace":
                sample_color = img.getpixel((max(0, left-2), max(0, top-2)))
                draw = ImageDraw.Draw(img)
                draw.rectangle([left, top, right, bottom], fill=sample_color)
                
            if mode == "replace":
                replacement_text = user_data.get("ai_watermark_replace", "")
                sample_color = img.getpixel((max(0, left-2), max(0, top-2)))
                draw = ImageDraw.Draw(img)
                draw.rectangle([left, top, right, bottom], fill=sample_color)
                
                if replacement_text:
                    font = None
                    try:
                        font = ImageFont.truetype("arial.ttf", size=int((bottom-top)*0.6))
                    except:
                        font = ImageFont.load_default()
                        
                    text_x = left + (right - left) // 2
                    text_y = top + (bottom - top) // 2
                    brightness = sum(sample_color) / 3
                    text_color = (0,0,0) if brightness > 128 else (255,255,255)
                    draw.text((text_x, text_y), replacement_text, fill=text_color, font=font, anchor="mm")
        except Exception as ex:
            print(f"[Tenant {chat_id}] Failed to parse Gemini response: {ex}")
            return message.media
                    
        out_path = f"processed_{message.id}_{chat_id}.png"
        img.save(out_path)
        print(f"[Tenant {chat_id}] AI Watermark processing complete.")
        return out_path
        
    except Exception as e:
        print(f"[Tenant {chat_id}] AI Watermark error: {e}")
        return message.media
    finally:
        if img:
            try: img.close()
            except: pass
        if preview:
            try: preview.close()
            except: pass
        if temp_path and os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass
        trim_memory()



async def resolve_target_entity(client, target_raw):
    if not target_raw or not client:
        return None
    target_clean = str(target_raw).strip()
    if not target_clean:
        return None

    import re
    # 1. Private channel URL: t.me/c/1234567890/456 -> -1001234567890
    m_c = re.search(r't\.me/c/(\d+)', target_clean)
    if m_c:
        target_clean = f"-100{m_c.group(1)}"
    else:
        # Public channel URL: t.me/username -> @username
        m_pub = re.search(r't\.me/([a-zA-Z0-9_]+)', target_clean)
        if m_pub and not target_clean.startswith('t.me/+') and '/+' not in target_clean and '/joinchat/' not in target_clean:
            target_clean = f"@{m_pub.group(1)}"

    # 2. Positive digits >= 9 -> convert to -100 ID
    digits_only = target_clean.lstrip('-')
    if digits_only.isdigit() and len(digits_only) >= 9 and not target_clean.startswith('-100'):
        target_clean = f"-100{digits_only}"

    cache = getattr(client, '_channel_cache', {})

    # 3. Check client cache with variants
    variants = [target_clean, target_clean.lower()]
    if target_clean.startswith('@'):
        variants.append(target_clean.lstrip('@').lower())
    else:
        variants.append(f"@{target_clean.lower()}")

    try:
        t_int = int(target_clean)
        variants.append(t_int)
        if str(t_int).startswith('-100'):
            variants.append(int(str(t_int)[4:]))
            variants.append(str(t_int)[4:])
    except ValueError:
        pass

    for v in variants:
        if v in cache:
            return cache[v]

    # 4. Resolve via client.get_entity and cache it
    try:
        entity = None
        try:
            entity = await client.get_entity(int(target_clean))
        except ValueError:
            entity = await client.get_entity(target_clean)
        if entity:
            cache[target_clean] = entity
            cache[target_clean.lower()] = entity
            uname = getattr(entity, 'username', None)
            if uname:
                cache[uname.lower()] = entity
                cache[f"@{uname.lower()}"] = entity
            return entity
    except Exception as e:
        print(f"[TARGET RESOLVE] Notice: Could not resolve target {target_clean}: {e}")

    # 5. Fallback: return as int or string
    try:
        return int(target_clean)
    except ValueError:
        return target_clean


async def execute_forward(message, chat_id, user_data):
    async with forward_semaphore:
        try:
            return await _do_execute_forward(message, chat_id, user_data)
        except Exception as e:
            print(f"[Tenant {chat_id}] Error in execute_forward: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

async def _do_execute_forward(message, chat_id, user_data):
    import os
    from database_manager import save_user_data

    if isinstance(message, list):
        if not message:
            return
        msg = message[0]
    else:
        msg = message

    target_channels = user_data.get('targets', [])
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if str(chat_id) == admin_id and not target_channels:
        env_targets = os.getenv("TARGET_CHANNELS") or os.getenv("TARGET_CHANNEL")
        if env_targets:
            target_channels = [t.strip() for t in env_targets.split(",") if t.strip()]
    target_channels = [str(t).strip() for t in target_channels if str(t).strip()]

    # --- VOICE NOTE FILTER ---
    if (getattr(msg, 'voice', None) or getattr(msg, 'audio', None)) and user_data.get('disable_voicenotes', False):
        print(f"[Tenant {chat_id}] Message is a voice note or audio file. Skipping due to settings.")
        return
    
    modified_text = apply_rules(getattr(msg, 'text', '') or '', user_data)
    media_to_send = getattr(msg, 'media', None)
    
    client = active_clients.get(chat_id)
    if not client:
        print(f"[Tenant {chat_id}] Cannot forward: client not in active_clients.")
        return

    if media_to_send:
        from telethon.tl.types import MessageMediaPhoto
        from telethon.tl.types import MessageMediaDocument
        is_photo = isinstance(media_to_send, MessageMediaPhoto)
        is_video = getattr(message, 'video', None) is not None

        if is_photo:
            is_enabled = user_data.get("image_override_enabled", True)
            if is_enabled and (user_data.get("image_swap_path", "").strip() or user_data.get("image_swap_url", "").strip()):
                image_swap_path = user_data.get("image_swap_path", "").strip()
                image_swap_url = user_data.get("image_swap_url", "").strip()

                if image_swap_path and os.path.exists(image_swap_path):
                    # Cache check
                    cache_key = f"{chat_id}_image_{image_swap_path}"
                    if cache_key in media_cache_memory:
                        media_to_send = media_cache_memory[cache_key]
                    else:
                        media_to_send = image_swap_path
                elif image_swap_url:
                    media_to_send = image_swap_url
            else:
                # If standard image override is OFF, process AI watermark if enabled
                mode = user_data.get("ai_watermark_mode", "off")
                if mode != "off":
                    media_to_send = await ai_process_image(client, message, chat_id, user_data)
                    
        elif is_video:
            is_vid_enabled = user_data.get("video_override_enabled", True)
            if is_vid_enabled and (user_data.get("video_swap_path", "").strip() or user_data.get("video_swap_url", "").strip()):
                video_swap_path = user_data.get("video_swap_path", "").strip()
                video_swap_url = user_data.get("video_swap_url", "").strip()
                
                if video_swap_path and os.path.exists(video_swap_path):
                    cache_key = f"{chat_id}_video_{video_swap_path}"
                    if cache_key in media_cache_memory:
                        media_to_send = media_cache_memory[cache_key]
                    else:
                        media_to_send = video_swap_path
                elif video_swap_url:
                    media_to_send = video_swap_url
    
    smart_delay = user_data.get("smart_delay_enabled", False)
    if smart_delay:
        import random
        import asyncio
        delay_seconds = random.randint(60, 180)
        print(f"[Tenant {chat_id}] Smart Delay: Waiting {delay_seconds} seconds before forwarding...")
        await asyncio.sleep(delay_seconds)
        
    downloaded_restricted_media = None
    
    # CTA Text Appender (PRO)
    # User accounts cannot send inline buttons, so we append them as formatted text
    if user_data.get("cta_buttons") and is_pro(chat_id):
        toggles = get_feature_toggles()
        if toggles.get("cta_buttons_unlocked", True):
            cta_text = "\n\n"
            for btn in user_data["cta_buttons"]:
                cta_text += f"🔗 **[{btn['text']}]({btn['url']})**\n"
            
            if modified_text:
                modified_text += cta_text
            else:
                if message.text:
                    modified_text = message.text + cta_text
                else:
                    modified_text = cta_text

    fwd_msg_id = getattr(msg, 'id', None)
    if fwd_msg_id:
        fwd_origin = get_canonical_id(getattr(msg, 'chat_id', None) or getattr(msg, 'peer_id', None))
        fwd_key = f"fwd_{chat_id}_{fwd_origin}_{fwd_msg_id}"
        if fwd_key in processed_messages_cache:
            if time.time() - processed_messages_cache[fwd_key] < 180:
                print(f"[Tenant {chat_id}] Message {fwd_msg_id} was already forwarded to targets. Skipping duplicate.")
                return
        processed_messages_cache[fwd_key] = time.time()

    try:
        success = False
        orig_canonical = get_canonical_id(getattr(msg, 'chat_id', None) or getattr(msg, 'peer_id', None))
        seen_target_ids = set()
        for target in target_channels:
            target_clean = str(target).strip()
            if not target_clean:
                continue

            target_pre = get_canonical_id(target_clean)
            if target_pre and target_pre == orig_canonical:
                continue
            if target_pre and target_pre in seen_target_ids:
                continue

            t = await resolve_target_entity(client, target_clean)
            if t is None:
                continue

            # Loop guard & duplicate target guard
            t_canonical = get_canonical_id(t)
            if orig_canonical and t_canonical and t_canonical == orig_canonical:
                continue
            if t_canonical:
                if t_canonical in seen_target_ids:
                    print(f"[Tenant {chat_id}] Target {target} ({t_canonical}) already received this post. Skipping duplicate.")
                    continue
                seen_target_ids.add(t_canonical)
            if target_pre:
                seen_target_ids.add(target_pre)
                
            try:
                sent = None
                if media_to_send and not isinstance(media_to_send, MessageMediaWebPage):
                    if media_to_send == getattr(msg, 'media', None):
                        if downloaded_restricted_media:
                            sent = await client.send_file(t, downloaded_restricted_media, caption=modified_text)
                        else:
                            try:
                                sent = await client.send_message(t, modified_text, file=msg)
                            except Exception as forward_err:
                                err_str = str(forward_err).lower()
                                if "protected chat" in err_str or "restricted" in err_str or "chatforwardsrestricted" in err_str:
                                    print(f"[Tenant {chat_id}] Source chat is restricted, preparing media download...")
                                    file_size = 0
                                    doc = getattr(msg, 'document', None)
                                    if doc:
                                        file_size = getattr(doc, 'size', 0)
                                    MAX_BYTES = 25 * 1024 * 1024  # 25MB safety limit
                                    if file_size > MAX_BYTES:
                                        print(f"[Tenant {chat_id}] Media is {file_size / (1024*1024):.1f}MB (over 25MB limit). Forwarding text only to prevent crash.")
                                        sent = await client.send_message(t, modified_text or "[Large Media Omitted]")
                                    else:
                                        try:
                                            async with restricted_download_semaphore:
                                                downloaded_restricted_media = await asyncio.wait_for(
                                                    client.download_media(msg, file=f"restricted_{msg.id}_{chat_id}"),
                                                    timeout=60
                                                )
                                            if downloaded_restricted_media and os.path.exists(downloaded_restricted_media):
                                                sent = await client.send_file(t, downloaded_restricted_media, caption=modified_text)
                                            else:
                                                raise forward_err
                                        except asyncio.TimeoutError:
                                            print(f"[Tenant {chat_id}] Media download timed out after 60s. Forwarding text fallback.")
                                            sent = await client.send_message(t, modified_text or "")
                                else:
                                    raise forward_err
                    else:
                        # Sending a local file or URL override
                        sent = await client.send_file(t, media_to_send, caption=modified_text)
                        # Cache the sent media so we don't upload the file again
                        if sent and sent.media and isinstance(media_to_send, str) and os.path.exists(media_to_send):
                            if len(media_cache_memory) > 25:
                                media_cache_memory.clear()
                            if is_photo:
                                media_cache_memory[f"{chat_id}_image_{media_to_send}"] = sent.media
                            elif is_video:
                                media_cache_memory[f"{chat_id}_video_{media_to_send}"] = sent.media
                else:
                    if modified_text:
                        sent = await client.send_message(t, modified_text, link_preview=True)
                
                # SAVE MAPPING FOR MIRROR DELETION
                if sent and getattr(sent, 'id', None):
                    try:
                        save_message_map(chat_id, msg.chat_id, msg.id, target, sent.id)
                    except Exception:
                        pass
                success = True
            except Exception as e:
                print(f"[Tenant {chat_id}] Failed to forward cleanly to {t}: {e}")
                # ONLY fallback if message was NOT sent at all
                if not sent and modified_text:
                    try:
                        sent = await client.send_message(t, modified_text)
                        if sent and getattr(sent, 'id', None):
                            try:
                                save_message_map(chat_id, msg.chat_id, msg.id, target, sent.id)
                            except Exception:
                                pass
                        success = True
                    except Exception as fallback_e:
                        print(f"[Tenant {chat_id}] Fallback failed for {t}: {fallback_e}")
                        
        if success:
            print(f"[Tenant {chat_id}] Message {getattr(msg, 'id', '')} forwarded successfully.")
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
                
        # Cleanup restricted downloads
        if 'downloaded_restricted_media' in locals() and downloaded_restricted_media and os.path.exists(downloaded_restricted_media):
            try:
                os.remove(downloaded_restricted_media)
            except:
                pass

        trim_memory()


async def handle_message(event, chat_id):
    print(f"[DEBUG-ALL-MESSAGES] Tenant {chat_id} received message from {event.chat_id}")
    from database_manager import save_user_data
    user_data = await asyncio.to_thread(get_user_data, chat_id)
    
    # --- PRO EXPIRATION KILL-SWITCH ---
    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
    if str(chat_id) != admin_id:
        is_paused = user_data.get('pro_paused') or (user_data.get('pro_expired_at') and not user_data.get('is_pro'))
        if is_paused:
            print(f"[Tenant {chat_id}] FORWARDING FROZEN: PRO subscription expired. Message {event.message.id} dropped.")
            last_alert = user_data.get('last_freeze_notice_time', 0)
            if time.time() - last_alert > 43200:
                user_data['last_freeze_notice_time'] = time.time()
                await asyncio.to_thread(save_user_data, chat_id, user_data)
                from database_manager import send_telegram_alert
                freeze_msg = (
                    "⛔ <b>WP RELAY: FORWARDING PAUSED</b>\n\n"
                    "A new post was detected in your source channel, but <b>forwarding is currently halted</b> because your PRO subscription has expired.\n\n"
                    "All routing, anti-ban protection, and custom modifications are frozen.\n\n"
                    "👉 Contact Administrator @apklord55 to unpause your channels."
                )
                await asyncio.to_thread(send_telegram_alert, chat_id, freeze_msg, "💎 UNPAUSE FORWARDER ↗", "https://t.me/apklord55")
            return

    source_channels = user_data.get('sources', [])
    target_channels = user_data.get('targets', [])

    # If Admin has empty sources/targets in DB, fall back to .env
    if str(chat_id) == admin_id:
        if not source_channels and os.getenv("SOURCE_CHANNELS"):
            source_channels = [s.strip() for s in os.getenv("SOURCE_CHANNELS").split(",") if s.strip()]
        if not target_channels and (os.getenv("TARGET_CHANNELS") or os.getenv("TARGET_CHANNEL")):
            env_targets = os.getenv("TARGET_CHANNELS") or os.getenv("TARGET_CHANNEL")
            target_channels = [t.strip() for t in env_targets.split(",") if t.strip()]

    if not source_channels or not target_channels:
        return

    # Loop prevention: Ignore messages originating from one of the tenant's target channels
    incoming_id = event.chat_id
    incoming_str = str(incoming_id)
    target_clean_set = set()
    for t in target_channels:
        ts = str(t).strip()
        if not ts:
            continue
        target_clean_set.add(ts)
        target_clean_set.add(ts.lstrip('-'))
        if ts.startswith('-100'):
            target_clean_set.add(ts[4:])
        elif ts.lstrip('-').isdigit():
            target_clean_set.add(f"-100{ts.lstrip('-')}")

    if incoming_str in target_clean_set or incoming_str.lstrip('-') in target_clean_set:
        return

    is_source = False
    # Build all possible representations of the incoming channel ID
    incoming_variants = {incoming_str}
    if incoming_str.startswith('-100'):
        incoming_variants.add(incoming_str[4:])   # bare digits without -100
        incoming_variants.add(incoming_str[1:])   # without leading dash
    elif incoming_str.lstrip('-').isdigit():
        incoming_variants.add(f"-100{incoming_str.lstrip('-')}")  # add -100 prefix

    # Retrieve incoming username
    incoming_uname = None
    if hasattr(event, 'chat') and event.chat and getattr(event.chat, 'username', None):
        incoming_uname = event.chat.username.lower()
    else:
        try:
            c_obj = await event.get_chat()
            if c_obj and getattr(c_obj, 'username', None):
                incoming_uname = c_obj.username.lower()
        except Exception:
            pass

    client = active_clients.get(chat_id)
    cache = getattr(client, '_channel_cache', {}) if client else {}

    for src in source_channels:
        src_str = str(src).strip()
        if not src_str:
            continue

        # A) Direct ID match
        if src_str in incoming_variants or src_str.lstrip('-') in {v.lstrip('-') for v in incoming_variants}:
            is_source = True
            print(f"[Tenant {chat_id}] [MATCH-ID] {src_str} matched {incoming_str}")
            break

        # B) Match via entity cache
        src_lower = src_str.lower().strip()
        if src_lower in cache:
            resolved_id = cache[src_lower] if isinstance(cache[src_lower], int) else getattr(cache[src_lower], 'id', None)
            if resolved_id and (str(resolved_id) in incoming_variants or str(resolved_id).lstrip('-') in {v.lstrip('-') for v in incoming_variants}):
                is_source = True
                print(f"[Tenant {chat_id}] [MATCH-CACHE] {src_str} ({resolved_id}) matched {incoming_str}")
                break

        # C) Telegram URL / Invite Link
        m_c = re.search(r't\.me/c/(\d+)', src_str)
        if m_c:
            c_digits = m_c.group(1)
            c_full = f"-100{c_digits}"
            if c_full in incoming_variants or c_digits in incoming_variants:
                is_source = True
                print(f"[Tenant {chat_id}] [MATCH-URL-C] {src_str} matched {incoming_str}")
                break

        m_pub = re.search(r't\.me/([a-zA-Z0-9_]+)', src_str)
        if m_pub and not src_str.startswith('t.me/+') and '/+' not in src_str and '/joinchat/' not in src_str:
            extracted_uname = m_pub.group(1).lower()
            if incoming_uname and (extracted_uname == incoming_uname or f"@{extracted_uname}" == incoming_uname):
                is_source = True
                print(f"[Tenant {chat_id}] [MATCH-URL-PUB] {src_str} matched @{incoming_uname}")
                break

        # Known invite link for WP Community
        if '+vYdMOKg3Gl5hMTNk' in src_str or 'vYdMOKg3Gl5hMTNk' in src_str:
            if incoming_str in {'-1002257843688', '2257843688'}:
                is_source = True
                print(f"[Tenant {chat_id}] [MATCH-INVITE-LINK] {src_str} matched {incoming_str}")
                break

        # D) Username match
        src_uname = src_lower.lstrip('@')
        if incoming_uname and (src_uname == incoming_uname or src_lower == f"@{incoming_uname}"):
            is_source = True
            print(f"[Tenant {chat_id}] [MATCH-USERNAME] {src_str} matched @{incoming_uname}")
            break

    if not is_source:
        return
        
    msg_id = getattr(event.message, 'id', None)
    if msg_id and is_duplicate_message(chat_id, event.chat_id, msg_id):
        print(f"[Tenant {chat_id}] Ignoring DUPLICATE message {msg_id} from {event.chat_id}")
        return

    print(f"[Tenant {chat_id}] Received message from source: {event.chat_id}")
    
    drip_interval = user_data.get("drip_interval", 0)
    in_sleep = is_in_sleep_mode(user_data)
    
    if (drip_interval and drip_interval > 0) or in_sleep:
        queue = user_data.get("drip_queue", [])
        if any(item.get("msg_id") == event.message.id and get_canonical_id(item.get("source_chat_id")) == get_canonical_id(event.chat_id) for item in queue):
            print(f"[Tenant {chat_id}] Message {event.message.id} is already in drip queue. Skipping duplicate queueing.")
            return

        preview = event.message.text[:50] + "..." if event.message.text else "[Media/No Text]"
        queue.append({
            "msg_id": event.message.id, 
            "source_chat_id": event.chat_id,
            "preview": preview,
            "added_at": time.time()
        })
        user_data["drip_queue"] = queue
        await asyncio.to_thread(save_user_data, chat_id, user_data)
        reason = "Sleep Mode" if in_sleep else "Drip Posting"
        print(f"[Tenant {chat_id}] Message queued for {reason}. (Queue size: {len(queue)})")
        return

    await execute_forward(event.message, chat_id, user_data)
        
import uuid
import signal

INSTANCE_ID = str(uuid.uuid4())[:8]

async def acquire_or_wait_leader_lock():
    try:
        from database_manager import supabase
        if not supabase:
            return True
        for attempt in range(6):
            try:
                res = await asyncio.to_thread(lambda: supabase.table('platform_state').select('value').eq('key', 'forwarder_leader').execute())
                if res.data:
                    leader = res.data[0].get('value', {})
                    last_seen = leader.get('timestamp', 0)
                    other_instance = leader.get('instance_id')
                    if other_instance and other_instance != INSTANCE_ID and (time.time() - last_seen < 15):
                        print(f"[LEADER LOCK] Old instance {other_instance} still active ({int(time.time() - last_seen)}s ago). Waiting for graceful shutdown...")
                        await asyncio.sleep(5)
                        continue
                await asyncio.to_thread(lambda: supabase.table('platform_state').upsert({
                    'key': 'forwarder_leader',
                    'value': {'instance_id': INSTANCE_ID, 'timestamp': time.time()}
                }).execute())
                print(f"[LEADER LOCK] Acquired leadership as instance {INSTANCE_ID}.")
                return True
            except Exception as e:
                print(f"[LEADER LOCK] Check attempt error: {e}")
                await asyncio.sleep(3)
    except Exception as outer_e:
        print(f"[LEADER LOCK] Exception: {outer_e}")
    return True

async def update_leader_lock():
    try:
        from database_manager import supabase
        if supabase:
            await asyncio.to_thread(lambda: supabase.table('platform_state').upsert({
                'key': 'forwarder_leader',
                'value': {'instance_id': INSTANCE_ID, 'timestamp': time.time()}
            }).execute())
    except Exception:
        pass

async def graceful_shutdown():
    print("[SHUTDOWN] Gracefully disconnecting all Telegram sessions...")
    for cid, client in list(active_clients.items()):
        try:
            await client.disconnect()
        except Exception:
            pass
    active_clients.clear()

async def monitor_users():
    print(f"Starting Multi-Tenant Forwarding Engine [{INSTANCE_ID}]...")
    try:
        with open('status.json', 'w') as f:
            json.dump({"last_seen": time.time(), "status": "starting", "instance_id": INSTANCE_ID}, f)
    except Exception:
        pass
    await acquire_or_wait_leader_lock()
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(graceful_shutdown()))
            except (NotImplementedError, AttributeError):
                pass
    except Exception:
        pass

    last_leader_update = 0
    last_mem_trim = time.time()

    while True:
        try:
            if time.time() - last_leader_update >= 15:
                last_leader_update = time.time()
                await update_leader_lock()

            # 1. Write the main heartbeat so the bot knows the engine is alive
            with open('status.json', 'w') as f:
                json.dump({"last_seen": time.time(), "status": "online"}, f)
                
            # 2. Check all tenants
            all_users = await asyncio.to_thread(get_all_users)
            
            from database_manager import save_user_data
                        # Process Drip Queues
            for chat_id, client in list(active_clients.items()):
                udata = await asyncio.to_thread(get_user_data, chat_id)
                
                # Process Manual Extract Requests
                extract_url = udata.get("manual_extract_url")
                if extract_url:
                    udata["manual_extract_url"] = ""
                    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
                    if str(chat_id) != admin_id and (udata.get('pro_paused') or (udata.get('pro_expired_at') and not udata.get('is_pro'))):
                        udata["manual_extract_result"] = "❌ PRO Subscription Expired. Feature paused until renewed. Contact @apklord55."
                        await asyncio.to_thread(save_user_data, chat_id, udata)
                        continue
                    try:
                        import re
                        m_priv = re.search(r't\.me/c/(\d+)/(\d+)', extract_url)
                        m_pub = re.search(r't\.me/([a-zA-Z0-9_]+)/(\d+)', extract_url)
                        
                        group_id = None
                        msg_id = None
                        if m_priv:
                            group_id = int("-100" + m_priv.group(1))
                            msg_id = int(m_priv.group(2))
                        elif m_pub:
                            group_id = m_pub.group(1)
                            msg_id = int(m_pub.group(2))
                            
                        if group_id and msg_id:
                            msgs = await client.get_messages(group_id, ids=[msg_id])
                            if msgs and msgs[0]:
                                msg_obj = msgs[0]
                                text = msg_obj.text or ""
                                media_path = ""
                                limit_msg = ""
                                
                                user_is_pro = is_pro(chat_id) or str(chat_id) == str(os.getenv("ADMIN_ID", "")).strip()
                                
                                if msg_obj.media:
                                    can_download = True
                                    is_vid = bool(msg_obj.video or getattr(msg_obj, 'video_note', None) or (getattr(msg_obj, 'document', None) and getattr(msg_obj.document, 'mime_type', '').startswith('video/')))
                                    
                                    import datetime
                                    today_str = datetime.date.today().isoformat()
                                    
                                    if is_vid:
                                        # Strict 1 video per day to preserve server bandwidth
                                        last_vid_date = udata.get("manual_video_date", "")
                                        vid_count = udata.get("manual_video_count", 0)
                                        if last_vid_date != today_str:
                                            vid_count = 0
                                            udata["manual_video_date"] = today_str
                                            
                                        if vid_count >= 1:
                                            can_download = False
                                            limit_msg = "\n\n⚠️ **Notice:** Daily bandwidth limit reached (1/1 video per day). Video was not extracted."
                                        else:
                                            vid_count += 1
                                            udata["manual_video_count"] = vid_count
                                            limit_msg = "\n\n*(Daily server bandwidth: Video 1/1)*"
                                    elif not user_is_pro:
                                        # Free tier image/doc limit
                                        last_date = udata.get("manual_extract_date", "")
                                        extract_count = udata.get("manual_extract_count", 0)
                                        if last_date != today_str:
                                            extract_count = 0
                                            udata["manual_extract_date"] = today_str
                                        
                                        if extract_count >= 5:
                                            can_download = False
                                            limit_msg = "\n\n⚠️ **Notice:** Daily free limit reached (5/5). Upgrade to PRO 💎 for unlimited extractions."
                                        else:
                                            extract_count += 1
                                            udata["manual_extract_count"] = extract_count
                                            limit_msg = f"\n\n*(Daily free tier: {extract_count}/5)*"
                                    
                                    if can_download:
                                        try:
                                            os.makedirs("temp_extract", exist_ok=True)
                                            dest_prefix = f"temp_extract/extract_{chat_id}_{msg_id}"
                                            downloaded = await client.download_media(msg_obj, file=dest_prefix)
                                            if downloaded and os.path.exists(downloaded):
                                                media_path = downloaded
                                        except Exception as down_err:
                                            print(f"[Tenant {chat_id}] Media download error: {down_err}")
                                            if is_vid:
                                                udata["manual_video_count"] = max(0, vid_count - 1)
                                            limit_msg = f"\n\n⚠️ **Notice:** Failed to download media: {str(down_err)}"
                                        
                                udata["manual_extract_result"] = f"**Raw Extracted Output:**\n\n{text}{limit_msg}".strip()
                                udata["manual_extract_media"] = media_path or ""
                            else:
                                udata["manual_extract_result"] = "❌ Could not find that message."
                        else:
                            udata["manual_extract_result"] = "❌ Invalid link format."
                    except Exception as e:
                        udata["manual_extract_result"] = f"❌ Error extracting: {str(e)}"
                    await asyncio.to_thread(save_user_data, chat_id, udata)
                    continue

                interval = udata.get("drip_interval", 0)
                queue = udata.get("drip_queue", [])
                
                if queue and not is_in_sleep_mode(udata):
                    admin_id = str(os.getenv("ADMIN_ID", "5628105961"))
                    if str(chat_id) != admin_id and (udata.get('pro_paused') or (udata.get('pro_expired_at') and not udata.get('is_pro'))):
                        continue
                    last_drip = udata.get("last_drip_time", 0)
                    
                    # interval is stored in seconds directly
                    eff_interval = interval if interval > 0 else 2
                    
                    if time.time() - last_drip >= eff_interval:
                        item = queue.pop(0)
                        udata["last_drip_time"] = time.time()
                        udata["drip_queue"] = queue
                        await asyncio.to_thread(save_user_data, chat_id, udata)
                        
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
                                async for msg in client.iter_messages(tc, limit=100):
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
                    await asyncio.to_thread(save_user_data, chat_id, udata)
                    trim_memory()

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
                                max_fetch = min(auto_limit + 100, 200)
                                async for msg in client.iter_messages(tc, limit=max_fetch):
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
                        await asyncio.to_thread(save_user_data, chat_id, udata)
                        trim_memory()

            # Start new clients
            for chat_id in all_users:
                user_data = await asyncio.to_thread(get_user_data, chat_id)
                session_str = user_data.get("session_string", "")
                
                if session_str and chat_id not in active_clients:
                    if time.time() < tenant_cooldowns.get(chat_id, 0):
                        continue
                    print(f"Booting Engine for Tenant {chat_id}...")
                    try:
                        api_id = user_data.get("api_id")
                        api_hash = user_data.get("api_hash")
                        client = TelegramClient(StringSession(session_str), api_id, api_hash)
                        await client.connect()
                        
                        # Populate entity cache to make -100 IDs work for both sources and targets
                        try:
                            print(f"[Tenant {chat_id}] Fetching dialogs to populate entity cache...")
                            dialogs = await client.get_dialogs(limit=50)
                            cache = {}
                            for d in dialogs:
                                cache[d.id] = d.entity
                                d_str = str(d.id)
                                cache[d_str] = d.entity
                                cache[d_str.lstrip('-')] = d.entity
                                if d_str.startswith('-100'):
                                    cache[int(d_str[4:])] = d.entity
                                    cache[d_str[4:]] = d.entity
                                uname = getattr(d.entity, 'username', None)
                                if uname:
                                    cache[uname.lower()] = d.entity
                                    cache[f"@{uname.lower()}"] = d.entity
                            client._channel_cache = cache
                            del dialogs
                            trim_memory()
                        except Exception as e:
                            print(f"[Tenant {chat_id}] Failed to fetch dialogs: {e}")
                            
                        # CRITICAL: Properly remove ALL existing handlers to prevent stacking
                        for cb, ev in list(client.list_event_handlers()):
                            client.remove_event_handler(cb, ev)
                        
                        def _make_msg_handler(cid):
                            async def _msg_handler(e):
                                await handle_message(e, cid)
                            return _msg_handler

                        client.add_event_handler(
                            _make_msg_handler(chat_id),
                            events.NewMessage()
                        )
                        active_clients[chat_id] = client
                        print(f"✅ Engine ONLINE for Tenant {chat_id}")
                    except (AuthKeyUnregisteredError, AuthKeyInvalidError,
                            SessionRevokedError, SessionExpiredError, UserDeactivatedBanError) as e:
                        print(f"[Tenant {chat_id}] ⚠️ SESSION REVOKED: {e}. Pausing client.")
                        try: await client.disconnect()
                        except: pass
                        active_clients.pop(chat_id, None)
                        # Set 5-min retry cooldown in memory so we don't spam reconnect
                        tenant_cooldowns[chat_id] = time.time() + 300
                        try:
                            from database_manager import send_telegram_alert
                            msg = (
                                "⚠️ <b>Account Disconnected!</b>\n\n"
                                "Your Telegram session was logged out or revoked from outside the bot "
                                "(e.g. you logged out on your phone or Telegram revoked your session).\n\n"
                                "Your forwarding engine has been paused.\n\n"
                                "👉 Please open the bot or mini app to reconnect your account."
                            )
                            send_telegram_alert(chat_id, msg)
                        except Exception as notify_err:
                            print(f"[Tenant {chat_id}] Failed to notify: {notify_err}")
                    except Exception as e:
                        err_str = str(type(e).__name__).lower() + str(e).lower()
                        is_session_error = any(x in err_str for x in [
                            "authkey", "session", "revoked", "expired", "deactivated",
                            "banned", "unregistered", "invalid", "struct", "unpack"
                        ])
                        if is_session_error:
                            print(f"[Tenant {chat_id}] ⚠️ SESSION ERROR on boot: {type(e).__name__}: {e}. Pausing client.")
                            try: await client.disconnect()
                            except: pass
                            active_clients.pop(chat_id, None)
                            tenant_cooldowns[chat_id] = time.time() + 300
                            try:
                                from database_manager import send_telegram_alert
                                msg = (
                                    "⚠️ <b>Account Disconnected!</b>\n\n"
                                    "Your Telegram session had a connection error.\n\n"
                                    "Your forwarding engine has been paused.\n\n"
                                    "👉 Please reconnect your account if this persists."
                                )
                                send_telegram_alert(chat_id, msg)
                            except Exception as notify_err:
                                print(f"[Tenant {chat_id}] Failed to notify: {notify_err}")
                        else:
                            print(f"❌ Failed to boot engine for {chat_id}: {type(e).__name__}: {e}")

            # Stop disconnected clients + Health check for revoked sessions
            for chat_id in list(active_clients.keys()):
                client = active_clients[chat_id]
                user_data = await asyncio.to_thread(get_user_data, chat_id)

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
                        active_clients.pop(chat_id, None)
                        tenant_cooldowns[chat_id] = time.time() + 300
                        try:
                            from database_manager import send_telegram_alert
                            msg = (
                                "⚠️ <b>Account Disconnected!</b>\n\n"
                                "Your Telegram session was disconnected.\n\n"
                                "👉 Please open the bot or mini app to reconnect."
                            )
                            send_telegram_alert(chat_id, msg)
                        except Exception as notify_err:
                            print(f"[Tenant {chat_id}] Failed to notify: {notify_err}")
                        continue
                    except (asyncio.CancelledError, Exception):
                        pass  # Other ping errors (network, timeout, cancellation) are non-fatal

                if not user_data.get("session_string"):
                    print(f"Shutting down Engine for Tenant {chat_id}...")
                    client = active_clients.pop(chat_id)
                    await client.disconnect()

        except Exception as e:
            print(f"Error in monitor loop: {e}")

        if time.time() - last_mem_trim >= 30:
            last_mem_trim = time.time()
            trim_memory()

        await asyncio.sleep(8)

if __name__ == '__main__':
    asyncio.run(monitor_users())




