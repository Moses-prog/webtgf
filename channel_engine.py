import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CHANNEL = "@webtgfv1"
DEFAULT_BOT_USERNAME = "wprelaybot"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOPILOT_FILE = os.path.join(BASE_DIR, "channel_autopilot.json")
LOCK_FILE = os.path.join(BASE_DIR, "autopilot.lock")

# Concise System Knowledge Base for WP Relay
WP_RELAY_KNOWLEDGE = """
You are the Growth & Engineering Lead for WP Relay (@wprelaybot), the enterprise Telegram channel forwarding, rewriting, and automation bot.
Official Channel: @webtgfv1
Bot Handle: @wprelaybot

WP RELAY CORE FEATURES:
1. Anti-Ban Human Jitter Delay: Randomized delivery pause (8s-35s) mimicking natural human posting, dodging Telegram spam filters and FloodWait locks.
2. Global Link & Username Rewriter: Auto-swaps any competitor t.me link, website link, or @mention with the tenant's own handle and affiliate URL.
3. Dynamic Watermark Engine: Auto-stamps custom brand text or logos directly onto forwarded photos.
4. Interactive CTA Buttons: Appends clickable Telegram inline buttons ([ ⚡ Launch WP Relay Bot ], [ 💎 Upgrade to PRO ]) below forwarded messages.
5. Drip Posting Pacer: Queues and spaces out high-burst source drops so subscribers are never spammed.
6. Auto-Delete & Ephemeral Drops: Automatically wipes posts after X hours, creating VIP FOMO and keeping channels clutter-free.
7. Mirror Deletion & Live Sync: Instantly mirrors edits or message deletions made in source channels.
8. PRO Suite: Unlimited routing, custom video replacements, and dedicated high-speed forwarder workers.
"""

TOPIC_CATEGORIES = [
    {
        "id": "anti_ban",
        "title": "Anti-Ban Human Jitter",
        "topic": "Why instant 0-second forwarding triggers Telegram spam locks and how WP Relay's 8-30s Human Jitter Delay makes your forwarding 100% ban-proof."
    },
    {
        "id": "link_rewriting",
        "title": "Global Link Rewriter",
        "topic": "How to instantly monetize incoming content by automatically replacing competitor links and @mentions with your own handles and affiliate URLs."
    },
    {
        "id": "watermarking",
        "title": "Dynamic Watermarking",
        "topic": "How to protect brand ownership by auto-stamping your custom watermark onto every forwarded image."
    },
    {
        "id": "cta_buttons",
        "title": "Interactive CTA Buttons",
        "topic": "How adding clickable native inline buttons below every post skyrockets click-through rates to your VIP bots and affiliate links."
    },
    {
        "id": "drip_pacer",
        "title": "Drip Posting Pacer",
        "topic": "Why forwarding 15 posts at once causes subscribers to mute, and how WP Relay's Drip Pacer spaces them smoothly."
    },
    {
        "id": "auto_delete",
        "title": "Ephemeral Auto-Delete",
        "topic": "How VIP and signal channels use WP Relay's rolling auto-delete timers to create exclusivity, protect content, and eliminate clutter."
    },
    {
        "id": "pro_features",
        "title": "WP Relay PRO Power",
        "topic": "Why high-scale Telegram operators upgrade to PRO for custom video overrides, unlimited channels, and priority worker threads."
    },
    {
        "id": "telegram_growth",
        "title": "Multi-Channel Scaling",
        "topic": "How to syndicate content across multiple niche channels simultaneously with zero manual work."
    }
]

def get_autopilot_config():
    if os.path.exists(AUTOPILOT_FILE):
        try:
            with open(AUTOPILOT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "enabled": False,
        "frequency_hours": 12,
        "last_posted_at": 0,
        "topic_index": 0,
        "history": []
    }

def save_autopilot_config(cfg):
    try:
        with open(AUTOPILOT_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[AUTOPILOT] Error saving config: {e}")

def get_bot_status():
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        return {"configured": False, "valid": False, "error": "BOT_TOKEN not configured"}
    
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=6)
        d = r.json()
        if d.get("ok"):
            res = d.get("result", {})
            return {
                "configured": True,
                "valid": True,
                "bot_id": res.get("id"),
                "username": res.get("username"),
                "first_name": res.get("first_name")
            }
        else:
            return {
                "configured": True,
                "valid": False,
                "error": d.get("description", "Unauthorized")
            }
    except Exception as e:
        return {"configured": True, "valid": False, "error": str(e)}

def generate_channel_post(category_id=None, custom_prompt=None):
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables.")

    from google import genai
    client = genai.Client(api_key=gemini_key)

    chosen_category = None
    if category_id:
        for c in TOPIC_CATEGORIES:
            if c["id"] == category_id:
                chosen_category = c
                break

    if custom_prompt:
        subject = custom_prompt
    elif chosen_category:
        subject = chosen_category["topic"]
    else:
        import random
        chosen_category = random.choice(TOPIC_CATEGORIES)
        subject = chosen_category["topic"]

    system_prompt = f"""
{WP_RELAY_KNOWLEDGE}

TASK:
Write an ULTRA-CONCISE, visually captivating Telegram channel tip for @webtgfv1 about:
{subject}

STRICT FORMATTING & LENGTH CONSTRAINTS:
1. MAXIMUM 80-90 WORDS TOTAL. A subscriber must be able to scan and read the entire post in 10 seconds.
2. ABSOLUTELY NO LONG ESSAYS OR WALLS OF TEXT.
3. Clean, scannable formatting using Telegram HTML: <b>bold</b>, <i>italic</i>, <code>code</code>.
4. Exact layout to follow:

⚡ <b>WP RELAY TIP: [Punchy 3-5 Word Title]</b>

<i>[One sharp sentence on the mistake or challenge]</i>

• 🚨 <b>The Problem:</b> [1 punchy line]
• 🛡️ <b>The Solution:</b> [1 punchy line explaining the WP Relay feature]
• 💎 <b>The Win:</b> [1 punchy line on the benefit]

👉 <i>Configure in 30 seconds inside @wprelaybot:</i>

Output ONLY the formatted post. Do not include introductory notes or markdown codeblocks (no ```html).
"""

    models_to_try = ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
    last_err = None

    for m in models_to_try:
        try:
            resp = client.models.generate_content(
                model=m,
                contents=system_prompt
            )
            if resp and resp.text:
                text = resp.text.strip()
                if text.startswith("```html"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

                recommended_buttons = [
                    {"text": "⭐ LAUNCH WP RELAY BOT ⚡", "url": "https://t.me/wprelaybot?start=channel_tip", "style": "primary"},
                    {"text": "💎 UPGRADE TO PRO (VIP) ✅", "url": "https://t.me/wprelaybot?start=pro_upgrade", "style": "success"}
                ]

                # Generate AI Visual Card for the post
                image_path = os.path.join(BASE_DIR, "visual_card.png")
                try:
                    import card_designer
                    card_title = chosen_category["title"] if chosen_category else "PRO TIP"
                    card_sub = chosen_category["topic"] if chosen_category else "SMART HUMAN PACER FOR TELEGRAM"

                    clean_lines = [l.strip() for l in text.splitlines() if l.strip()]
                    if len(clean_lines) >= 1:
                        c0 = clean_lines[0].replace("<b>", "").replace("</b>", "").replace("⚡", "").replace("WP RELAY TIP:", "").replace("WP RELAY HACK:", "").strip()
                        if c0:
                            card_title = c0[:35]
                    if len(clean_lines) >= 2:
                        c1 = clean_lines[1].replace("<i>", "").replace("</i>", "").replace("<b>", "").replace("</b>", "").strip()
                        if c1:
                            card_sub = c1[:70]

                    card_designer.create_visual_card(
                        title=card_title,
                        subtitle=card_sub,
                        category="PRO TIP",
                        output_path=image_path
                    )
                except Exception as card_err:
                    print(f"[CARD GENERATION ERROR] {card_err}")
                    image_path = None

                return {
                    "text": text,
                    "buttons": recommended_buttons,
                    "model_used": m,
                    "image_path": image_path
                }
        except Exception as e:
            last_err = e

    raise RuntimeError(f"All Gemini models failed: {last_err}")

def publish_to_channel(text, buttons=None, pin=False, target_channel=DEFAULT_CHANNEL, disable_notification=False, image_path=None):
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is not configured in .env.")

    if not target_channel:
        target_channel = DEFAULT_CHANNEL

    target_channel = target_channel.strip()
    if not target_channel.startswith("@") and not target_channel.startswith("-100") and not target_channel.isdigit():
        target_channel = "@" + target_channel

    reply_markup = None
    if buttons and isinstance(buttons, list) and len(buttons) > 0:
        inline_keyboard = []
        for btn in buttons:
            txt = btn.get("text", "").strip()
            url = btn.get("url", "").strip()
            style = btn.get("style", "").strip()
            if txt and url:
                if not url.startswith(("http://", "https://", "t.me/")):
                    url = "https://" + url
                btn_dict = {"text": txt, "url": url}
                if style in ["primary", "success", "danger"]:
                    btn_dict["style"] = style
                inline_keyboard.append([btn_dict])
        
        if inline_keyboard:
            reply_markup = {"inline_keyboard": inline_keyboard}

    # Decide whether to send Photo or Text
    use_photo = bool(image_path and os.path.exists(image_path))
    res_data = None

    if use_photo:
        try:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            data = {
                "chat_id": target_channel,
                "caption": text,
                "parse_mode": "HTML",
                "disable_notification": str(bool(disable_notification)).lower()
            }
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)

            with open(image_path, "rb") as f:
                files = {"photo": f}
                r = requests.post(url, data=data, files=files, timeout=20)
                res_data = r.json()
        except Exception as photo_err:
            print(f"[PHOTO SEND ERROR] {photo_err}. Falling back to sendMessage.")
            use_photo = False

    if not use_photo or not (res_data and res_data.get("ok")):
        # Fallback to standard sendMessage
        payload = {
            "chat_id": target_channel,
            "text": text,
            "parse_mode": "HTML",
            "disable_notification": bool(disable_notification)
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=12)
        res_data = r.json()

    if not res_data.get("ok"):
        desc = res_data.get("description", "Unknown Telegram error")
        code = res_data.get("error_code")
        if code == 401:
            raise RuntimeError("Telegram Bot Token is unauthorized. Please verify the BOT_TOKEN in Admin Settings.")
        elif "chat not found" in desc.lower():
            raise RuntimeError(f"Target channel {target_channel} not found. Ensure the channel is public or the bot is added to it.")
        elif "not enough rights" in desc.lower() or "administrator" in desc.lower() or "can't post" in desc.lower():
            raise RuntimeError(f"Permission denied: Please ensure @wprelaybot is added as an ADMINISTRATOR in {target_channel} with 'Post Messages' permission.")
        else:
            raise RuntimeError(f"Telegram API Error ({code}): {desc}")

    sent_msg = res_data.get("result", {})
    msg_id = sent_msg.get("message_id")

    # Pin Message if requested
    pinned = False
    if pin and msg_id:
        try:
            pin_payload = {
                "chat_id": target_channel,
                "message_id": msg_id,
                "disable_notification": bool(disable_notification)
            }
            pr = requests.post(f"https://api.telegram.org/bot{token}/pinChatMessage", json=pin_payload, timeout=8)
            pin_data = pr.json()
        except Exception as e:
            print(f"[PIN ERROR] Failed to pin message {msg_id}: {e}")

    # Seed Reaction 🔥 (Social Proof Booster)
    try:
        rx_payload = {
            "chat_id": target_channel,
            "message_id": msg_id,
            "reaction": [{"type": "emoji", "emoji": "🔥"}],
            "is_big": False
        }
        requests.post(f"https://api.telegram.org/bot{token}/setMessageReaction", json=rx_payload, timeout=6)
    except Exception as rx_err:
        pass

    # Record history
    try:
        cfg = get_autopilot_config()
        cfg["last_posted_at"] = int(time.time())
        snippet = text[:100].replace("\n", " ") + "..."
        cfg["history"] = cfg.get("history", [])[-19:] + [{
            "timestamp": int(time.time()),
            "channel": target_channel,
            "message_id": msg_id,
            "pinned": pinned,
            "snippet": snippet
        }]
        save_autopilot_config(cfg)
    except Exception:
        pass

    return {
        "success": True,
        "message_id": msg_id,
        "channel": target_channel,
        "pinned": pinned
    }

def delete_channel_message(message_id, target_channel=DEFAULT_CHANNEL):
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is not configured in .env.")

    if not target_channel:
        target_channel = DEFAULT_CHANNEL

    r = requests.post(
        f"https://api.telegram.org/bot{token}/deleteMessage",
        json={"chat_id": target_channel, "message_id": int(message_id)},
        timeout=8
    )
    res = r.json()
    if not res.get("ok"):
        raise RuntimeError(res.get("description", "Failed to delete message"))
    return {"success": True, "deleted_id": message_id}

def run_autopilot_tick():
    now = int(time.time())

    # 1. Multi-process lock check (prevents two processes from running at the same second)
    if os.path.exists(LOCK_FILE):
        try:
            mtime = os.path.getmtime(LOCK_FILE)
            if now - mtime < 120:  # Lock held within 2 minutes
                return None
        except Exception:
            pass

    cfg = get_autopilot_config()
    if not cfg.get("enabled", False):
        return None

    freq_hours = max(1, int(cfg.get("frequency_hours", 12)))
    interval_sec = freq_hours * 3600
    last_run = int(cfg.get("last_posted_at", 0))

    if now - last_run < interval_sec:
        # Not time yet
        return None

    # 2. Acquire lock and pre-commit timestamp IMMEDIATELY to prevent simultaneous double-runs
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(now))
    except Exception:
        pass

    idx = cfg.get("topic_index", 0) % len(TOPIC_CATEGORIES)
    category = TOPIC_CATEGORIES[idx]

    # Pre-commit timestamp so no other thread/process can enter this block
    cfg["last_posted_at"] = now
    cfg["topic_index"] = (idx + 1) % len(TOPIC_CATEGORIES)
    save_autopilot_config(cfg)

    try:
        print(f"[AUTOPILOT] Generating scheduled post for category '{category['id']}'...")
        post_data = generate_channel_post(category_id=category["id"])
        
        should_pin = category["id"] in ["anti_ban", "pro_features"]

        result = publish_to_channel(
            text=post_data["text"],
            buttons=post_data["buttons"],
            pin=should_pin,
            target_channel=DEFAULT_CHANNEL,
            image_path=post_data.get("image_path")
        )
        print(f"[AUTOPILOT] Successfully published scheduled post: {result}")
        return result
    except Exception as e:
        print(f"[AUTOPILOT] Scheduled post error: {e}")
        return None
    finally:
        # Release lock file
        try:
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
        except Exception:
            pass
