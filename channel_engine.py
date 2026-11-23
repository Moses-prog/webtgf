import os
import json
import time
import re
import random
import threading
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CHANNEL = os.getenv("OFFICIAL_CHANNEL", "@webtgfv1").strip() or "@webtgfv1"
DEFAULT_BOT_USERNAME = os.getenv("BOT_USERNAME", "wprelaybot").strip() or "wprelaybot"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOPILOT_FILE = os.path.join(BASE_DIR, "channel_autopilot.json")
LOCK_FILE = os.path.join(BASE_DIR, "autopilot.lock")
REMINDER_COOLDOWN_SECONDS = 48 * 3600
JOINED_MEMBER_STATUSES = {"creator", "administrator", "member", "restricted"}
UNJOINED_MEMBER_STATUSES = {"left", "kicked"}
_REMINDER_SWEEP_LOCK = threading.Lock()

# Plain, clear knowledge base for WP Relay channel posts
WP_RELAY_KNOWLEDGE = """
You write short, practical Telegram channel posts for WP Relay (@wprelaybot), a bot that helps channel owners copy, clean up, and grow Telegram channels automatically.
Official Channel: @webtgfv1
Bot Handle: @wprelaybot

WHAT WP RELAY ACTUALLY DOES (explain in simple, everyday words):
1. Safe Human Delay: Waits 8 to 35 seconds before posting instead of blasting instantly, so Telegram does not flag your account for spam.
2. Auto Link & @Username Swap: Finds the original channel's links or @usernames and replaces them with your own links automatically.
3. Auto Watermark: Puts your logo or @channel name on forwarded photos so others cannot steal your visuals.
4. Clickable Buttons: Adds neat inline buttons under every post (Join VIP, Buy, Channel link, Bot link).
5. Post Spacing (Drip Mode): When a source drops 10 posts in a minute, spreads them out nicely so your subscribers do not mute your channel.
6. Auto-Delete Timer: Deletes posts automatically after 2h, 6h, 12h, or 24h so your feed stays clean and VIP drops feel urgent.
7. Live Edit & Delete Sync: If you fix a typo or delete a message in the source channel, your target channels update too.
8. One Source to Many Channels: Send one post into 10+ channels at once, with custom rules for each channel.
9. PRO Fast Mode: Smooth background workers, video swap, and unlimited channels without babysitting anything.
"""

STRATEGIC_PILLARS = [
    {
        "id": "anti_ban",
        "title": "Safe Delay & Anti-Ban",
        "description": "Why blasting posts in 0 seconds gets Telegram accounts restricted, and how a small 8-35 second human pause keeps your account safe."
    },
    {
        "id": "link_rewriting",
        "title": "Auto Link & @Name Swapping",
        "description": "How to replace another channel's links and @usernames with your own automatically without editing every post by hand."
    },
    {
        "id": "auto_delete",
        "title": "Auto-Delete & Clean Feeds",
        "description": "Using simple auto-delete timers (2h, 6h, 12h) to keep promo channels clean and get people checking posts before they disappear."
    },
    {
        "id": "watermarking",
        "title": "Photo Watermarks & Branding",
        "description": "Putting your own channel name or logo on images automatically so people know the post came from you."
    },
    {
        "id": "drip_pacer",
        "title": "Spacing Posts Out (No Spam)",
        "description": "Why dropping 15 messages back-to-back makes followers mute your channel, and how spacing them out keeps real views high."
    },
    {
        "id": "cta_buttons",
        "title": "Clickable Buttons Under Posts",
        "description": "Adding a clean button right below your post so readers can tap straight into your bot, VIP group, or website."
    },
    {
        "id": "multi_channel",
        "title": "Run Multiple Channels From One Source",
        "description": "Post once and let WP Relay copy, clean up, and customize the post across several channels at the same time."
    },
    {
        "id": "live_sync",
        "title": "Auto-Update Edits & Deletes",
        "description": "When the source fixes a mistake or removes a post, your channels update automatically with no extra work."
    },
    {
        "id": "algo_hacks",
        "title": "Getting More Organic Views",
        "description": "Simple habits—clean spacing, clear headlines, reactions, and pinning—that help more subscribers actually read your channel."
    },
    {
        "id": "pro_workers",
        "title": "Hands-Free PRO Automation",
        "description": "Running busy channels 24/7 with zero missed messages, custom video swaps, and faster routing."
    },
    {
        "id": "case_study",
        "title": "Real Channel Example",
        "description": "A short before-and-after story showing how a channel owner saved hours every week and got better views with WP Relay."
    },
    {
        "id": "myth_busters",
        "title": "Common Forwarding Mistakes",
        "description": "Simple mistakes almost every Telegram channel owner makes when forwarding posts, and the easy fix."
    }
]

# Keep TOPIC_CATEGORIES as an alias for backwards compatibility with web API & Mini App UI
TOPIC_CATEGORIES = STRATEGIC_PILLARS

EDITORIAL_FORMATS = [
    {
        "id": "case_study",
        "name": "Quick Before/After",
        "instruction": """
Write a short, realistic BEFORE & AFTER story in everyday words:
- Start with a bold plain hook: 📊 <b>Real Example: [Short relatable situation]</b>
- 1-2 short sentences on what used to waste time or hurt views.
- 1-2 short sentences on what changed once they set up WP Relay.
- 1 crisp closing line telling readers they can set it up in @wprelaybot.
"""
    },
    {
        "id": "myth_buster",
        "name": "Quick Reality Check",
        "instruction": """
Write a quick REALITY CHECK that clears up a bad habit:
- Start with: ⚡ <b>Quick Tip: [Plain surprising fact]</b>
- What most people do wrong (1 short sentence).
- Why it backfires and what works better instead (1-2 short sentences).
- 1 friendly closing line pointing to @wprelaybot.
"""
    },
    {
        "id": "stealth_playbook",
        "name": "3 Quick Steps",
        "instruction": """
Write a super clear 3-STEP CHECKLIST people can copy right now:
- Start with: ✅ <b>3 Quick Steps: [Clear outcome]</b>
- 1 short line saying why this helps.
- Bullet list with plain language:
  • <b>1.</b> [Simple action]
  • <b>2.</b> [Simple action]
  • <b>3.</b> [Simple action]
- 1 short closing line pointing to @wprelaybot.
"""
    },
    {
        "id": "security_alert",
        "name": "Account Safety Heads-Up",
        "instruction": """
Write a helpful SAFETY HEADS-UP (not dramatic fake urgency, just real advice):
- Start with: 🚨 <b>Heads-Up: [Common risk or ban trigger]</b>
- What gets accounts flagged or channels muted (1-2 simple sentences).
- The easy setting inside WP Relay that stops it (1-2 simple sentences).
- 1 crisp line pointing to @wprelaybot.
"""
    },
    {
        "id": "growth_teardown",
        "name": "One Smart Fix",
        "instruction": """
Write a straight-to-the-point TIP ABOUT ONE FIX:
- Start with: 💡 <b>[Plain Useful Title in 4-6 Words]</b>
- Name the exact headache channel owners deal with (1 short sentence).
- Show the simple automated setup that solves it (2 short sentences or bullets).
- 1 natural closing line pointing to @wprelaybot.
"""
    }
]

def sanitize_telegram_html(text):
    """Ensure text only contains Telegram-supported HTML tags and has balanced entities."""
    if not text:
        return ""
    # Convert unsupported list items and paragraphs to clean Telegram formatting
    text = re.sub(r'</?(?:ul|ol|p|div)>', '\n', text)
    text = re.sub(r'<li>\s*', '• ', text)
    text = re.sub(r'</li>', '\n', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    # Strip any forbidden tags
    text = re.sub(r'<(?!/?(?:b|i|u|s|code|pre|a|tg-spoiler)\b)[^>]+>', '', text)
    # Clean multiple consecutive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

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
    """
    Intelligently generates a completely unique, non-repeating Telegram channel post
    paired with custom contextual CTA buttons and a matching multi-theme visual card.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables.")

    from google import genai
    client = genai.Client(api_key=gemini_key)

    cfg = get_autopilot_config()
    history = cfg.get("history", [])

    # Extract recent post titles & snippets to prevent any thematic or structural repetition
    recent_titles = []
    for item in history[-12:]:
        t = item.get("title") or item.get("snippet", "")
        if t:
            recent_titles.append(t[:60])
    
    recent_history_context = ""
    if recent_titles:
        recent_history_context = "PREVIOUSLY PUBLISHED TOPICS (DO NOT REPEAT OR REHASH THESE EXACT ANGLES):\n"
        for i, rt in enumerate(recent_titles, 1):
            recent_history_context += f"{i}. {rt}\n"

    # Select Strategic Pillar
    chosen_pillar = None
    if category_id:
        for p in STRATEGIC_PILLARS:
            if p["id"] == category_id:
                chosen_pillar = p
                break
    
    if not chosen_pillar and not custom_prompt:
        # Intelligently select a pillar not used in the last 3 runs
        recent_cats = [h.get("category", "").lower() for h in history[-3:] if h.get("category")]
        eligible = [p for p in STRATEGIC_PILLARS if p["title"].lower() not in recent_cats]
        chosen_pillar = random.choice(eligible if eligible else STRATEGIC_PILLARS)

    # Select Dynamic Editorial Format
    chosen_format = random.choice(EDITORIAL_FORMATS)

    pillar_topic = chosen_pillar["description"] if chosen_pillar else (custom_prompt or "Telegram channel automation and monetization")
    pillar_title = chosen_pillar["title"] if chosen_pillar else "Telegram Growth"

    system_prompt = f"""
{WP_RELAY_KNOWLEDGE}

GOAL:
Write a short, easy-to-read Telegram post for @webtgfv1 that sounds like a real person giving practical advice — NOT a corporate ad or textbook.

TOPIC TO COVER:
"{pillar_title}": {pillar_topic}

FORMAT TO FOLLOW:
{chosen_format["instruction"]}

{recent_history_context}

WRITING RULES (VERY IMPORTANT):
1. WORD COUNT: Keep it tight — 55 to 85 WORDS TOTAL. Short paragraphs with clean line breaks so anyone can scan it in 5 seconds on mobile.
2. PLAIN, EVERYDAY WORDS ONLY:
   - Write like you are explaining something helpful to a friend who runs Telegram channels.
   - BANNED WORDS (NEVER use these or similar heavy buzzwords): arbitrage, syndication, ephemeral, heuristics, architecture, bottleneck, protocol, compounding, concurrency, enterprise, funnel, telemetry, leverage, seamless, unlock, revolutionize, skyrocket, game-changer, paradigm, ecosystem, monetization matrix.
   - Use simple words instead: "safe delay", "swap links", "auto-delete", "space posts out", "clean feed", "save time", "clickable button".
3. NATURAL VARIETY: Follow the FORMAT TO FOLLOW above cleanly (do NOT force every post into the same rigid template).
4. ALLOWED HTML TAGS ONLY: <b>, <i>, <code>, <s>, <u>, <a href="...">, <tg-spoiler>.
   NEVER use <ul>, <ol>, <li>, <p>, <div>, or markdown (*, #, **).
5. VISUAL CARD THEME (pick the closest match):
   - "cyber_cyan": Delay, spacing posts, general tips, or clean automation.
   - "crimson_alert": Safety tips, avoiding bans, or common mistakes.
   - "emerald_cash": Link swapping, buttons, or making money from channels.
   - "royal_purple": PRO plan features or hands-free speed.
   - "sunset_amber": Getting more views or growing engagement.
   - "stealth_mono": Running multiple channels or syncing edits/deletes.
6. CLEAR SHORT CARD TEXT & BUTTONS (keep card titles & buttons simple too, max 3-4 words).

OUTPUT FORMAT:
Return a strict JSON object with these EXACT keys:
{{
  "card_title": "SHORT 2-4 WORD HEADLINE (UPPERCASE, PLAIN WORDS)",
  "card_subtitle": "CLEAR 5-8 WORD BENEFIT (UPPERCASE, NO JARGON)",
  "category_badge": "2-3 WORD LABEL (e.g. QUICK TIP, REAL EXAMPLE, SAFETY TIP, 3 STEPS)",
  "theme": "one of: cyber_cyan, crimson_alert, emerald_cash, royal_purple, sunset_amber, stealth_mono",
  "feature_pills": ["PLAIN PILL 1", "PLAIN PILL 2", "PLAIN PILL 3"],
  "should_pin": false,
  "text": "Short, human Telegram post with clean <b>bold</b> highlights and spacing",
  "buttons": [
    {{"text": "⚡ Open WP Relay Bot", "url": "https://t.me/wprelaybot?start=channel_tip", "style": "primary"}},
    {{"text": "💎 Try PRO Plan", "url": "https://t.me/wprelaybot?start=pro_upgrade", "style": "success"}}
  ]
}}
"""

    models_to_try = ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
    last_err = None

    for m in models_to_try:
        try:
            resp = client.models.generate_content(
                model=m,
                contents=system_prompt,
                config={"response_mime_type": "application/json"}
            )
            if resp and resp.text:
                raw_text = resp.text.strip()
                # Clean any lingering markdown codeblocks if present
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                parsed = json.loads(raw_text)

                post_text = sanitize_telegram_html(parsed.get("text", ""))
                card_title = parsed.get("card_title", "WP RELAY").strip()
                card_subtitle = parsed.get("card_subtitle", "SIMPLE TELEGRAM CHANNEL AUTOMATION").strip()
                category_badge = parsed.get("category_badge", chosen_format["name"]).strip()
                theme = parsed.get("theme", "cyber_cyan").strip()
                feature_pills = parsed.get("feature_pills", ["SAFE DELAY", "POST SPACING", "BAN-SAFE"])
                should_pin = bool(parsed.get("should_pin", False))

                buttons = parsed.get("buttons") or [
                    {"text": "⚡ Open WP Relay Bot", "url": "https://t.me/wprelaybot?start=channel_tip", "style": "primary"},
                    {"text": "💎 Try PRO Plan", "url": "https://t.me/wprelaybot?start=pro_upgrade", "style": "success"}
                ]

                # Generate Dynamic Multi-Theme Visual Card
                image_path = os.path.join(BASE_DIR, "visual_card.png")
                try:
                    import card_designer
                    card_designer.create_visual_card(
                        title=card_title,
                        subtitle=card_subtitle,
                        category=category_badge,
                        theme=theme,
                        feature_pills=feature_pills,
                        output_path=image_path
                    )
                except Exception as card_err:
                    print(f"[CARD GENERATION ERROR] {card_err}")
                    image_path = None

                return {
                    "text": post_text,
                    "buttons": buttons,
                    "card_title": card_title,
                    "card_subtitle": card_subtitle,
                    "category_badge": category_badge,
                    "theme": theme,
                    "feature_pills": feature_pills,
                    "should_pin": should_pin,
                    "format_used": chosen_format["id"],
                    "model_used": m,
                    "image_path": image_path
                }
        except Exception as e:
            print(f"[MODEL ERROR] {m} failed: {e}")
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
    # Telegram photo captions have a hard limit of 1024 characters
    use_photo = bool(image_path and os.path.exists(image_path) and len(text) <= 1024)
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
            pinned = bool(pin_data.get("ok"))
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

    # Record history with rich deduplication metadata
    try:
        cfg = get_autopilot_config()
        cfg["last_posted_at"] = int(time.time())
        snippet = text[:100].replace("\n", " ") + "..."
        cfg["history"] = cfg.get("history", [])[-24:] + [{
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

    # Pre-commit timestamp so no other thread/process can enter this block
    cfg["last_posted_at"] = now
    save_autopilot_config(cfg)

    try:
        print("[AUTOPILOT] Intelligently generating next unique channel post...")
        # Autopilot chooses a fresh dynamic pillar and format
        post_data = generate_channel_post()
        
        should_pin = bool(post_data.get("should_pin", False))

        result = publish_to_channel(
            text=post_data["text"],
            buttons=post_data["buttons"],
            pin=should_pin,
            target_channel=DEFAULT_CHANNEL,
            image_path=post_data.get("image_path")
        )
        print(f"[AUTOPILOT] Successfully published dynamic scheduled post: {result}")
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


def normalize_telegram_url(raw_url):
    """Normalize @handle, t.me/slug, or bare username into a valid HTTPS URL for Telegram inline buttons."""
    val = str(raw_url or "").strip()
    if not val:
        return ""
    if val.startswith("@"):
        slug = val.lstrip("@").strip()
        return f"https://t.me/{slug}" if slug else ""
    if val.startswith(("http://", "https://")):
        return val
    if val.startswith(("t.me/", "telegram.me/")):
        return f"https://{val}"
    if re.fullmatch(r"[A-Za-z0-9_]{3,64}", val):
        return f"https://t.me/{val}"
    return f"https://{val}"


def extract_bot_handle_and_url(raw_handle):
    """Extract normalized (display_handle, https_url) from a bot @handle or link."""
    val = str(raw_handle or "").strip()
    if not val:
        return "", ""
    url = normalize_telegram_url(val)
    m = re.search(r"(?:t\.me|telegram\.me)/([A-Za-z0-9_]+)", url, re.IGNORECASE)
    if m:
        return f"@{m.group(1)}", url
    if re.fullmatch(r"@?[A-Za-z0-9_]{3,64}", val):
        return f"@{val.lstrip('@')}", url
    return val, url


def generate_broadcast_message(intent="custom", user_prompt="", bot_name="", bot_handle="", strip_emojis=True):
    """Generate plain-English HTML broadcast copy and suggested CTA button using Gemini."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY not found in environment")

    from google import genai
    client = genai.Client(api_key=gemini_key)

    suggested_btn_text = ""
    suggested_btn_url = ""
    intent = str(intent or "").strip().lower()

    if intent == "promote_bot":
        norm_handle, norm_url = extract_bot_handle_and_url(bot_handle)
        if not norm_handle or not norm_url:
            raise ValueError("Please enter a valid bot @username or t.me link.")
        clean_name = str(bot_name or "").strip() or norm_handle
        pitch = str(user_prompt or "").strip() or f"Check out {clean_name} ({norm_handle}), our new Telegram bot."
        prompt = (
            "You are writing a friendly message from WP Relay (@wprelaybot) to its active Telegram users to introduce another useful bot.\n"
            f"Bot Name: {clean_name}\n"
            f"Bot Handle or Link: {norm_handle}\n"
            f"What it does / Admin pitch: {pitch}\n\n"
            "Rules:\n"
            "- Write in simple, everyday conversational English (no big buzzwords, no hype, no corporate speak).\n"
            "- Open with 1 warm, clear sentence explaining why you are sharing it.\n"
            "- Add 3 short bullet points showing what users can do with it.\n"
            f"- End by inviting them to tap the button below or open {norm_handle}.\n"
            "- Keep it concise (55 to 90 words total).\n"
            "- Format using clean Telegram HTML with <b> and <code> tags only (no <ul>, <li>, <p>, markdown, or emojis).\n"
            "- Output ONLY the final message text."
        )
        suggested_btn_text = f"Try {clean_name}"
        suggested_btn_url = norm_url
    elif intent == "reconnect" or (not intent and (not user_prompt or "reconnect" in user_prompt.lower())):
        prompt = (
            "You are an assistant for a Telegram forwarder service. "
            "Write a clear, direct, and reassuring service alert to tenants. "
            "Explain that due to an IP and server security upgrade, Telegram paused message routing until they reconnect their session. "
            "Assure them that all their rules, swaps, channels, and settings are 100% saved and safe. "
            "Instruct them to tap the Reconnect button below or open @wprelaybot to log in again so message forwarding resumes right away. "
            "Use simple, plain English words only. No big or complicated words. "
            "Format using clean HTML with <b> and <code> tags and bullet points. "
            "IMPORTANT: Do NOT use any emojis whatsoever. Zero emojis. Output ONLY the message text itself."
        )
        suggested_btn_text = "Reconnect Telegram"
        suggested_btn_url = "https://t.me/wprelaybot"
    else:
        prompt = (
            "You are an assistant for a Telegram forwarder service. "
            f"Write a concise, friendly announcement based on these instructions: {user_prompt}. "
            "Use simple, plain English words only. No big or complicated words. "
            "Format using clean HTML with <b> tags and bullet points. "
            "IMPORTANT: Do NOT use any emojis whatsoever. Zero emojis. Output ONLY the message text itself."
        )

    models_to_try = ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-1.5-flash"]
    generated_text = None
    last_err = None
    for m in models_to_try:
        try:
            resp = client.models.generate_content(model=m, contents=prompt)
            if resp and resp.text:
                generated_text = resp.text.strip()
                break
        except Exception as e:
            last_err = e

    if not generated_text:
        raise RuntimeError(f"AI generation failed: {last_err}")

    clean_text = sanitize_telegram_html(generated_text)
    if strip_emojis:
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"
            "\U0001FA00-\U0001FA6F"
            "\U0001FA70-\U0001FAFF"
            "\U00002600-\U000026FF"
            "]+",
            flags=re.UNICODE,
        )
        clean_text = emoji_pattern.sub("", clean_text).strip()

    return {
        "generated_message": clean_text,
        "suggested_button_text": suggested_btn_text,
        "suggested_button_url": suggested_btn_url,
    }


OFFICIAL_CHANNEL_URL = normalize_telegram_url(DEFAULT_CHANNEL) or "https://t.me/webtgfv1"


def check_user_channel_membership(user_id, channel=None, bot_token=None):
    """Safely check if user_id is in the official Telegram channel via Bot API getChatMember."""
    token = (bot_token if bot_token is not None else os.getenv("BOT_TOKEN", "")).strip()
    if not token:
        return {"checked": False, "joined": None, "status": "no_token"}

    try:
        uid_int = int(str(user_id).strip())
    except (TypeError, ValueError):
        return {"checked": False, "joined": None, "status": "invalid_user_id", "skip_user": True}

    target_channel = (channel or DEFAULT_CHANNEL).strip() or DEFAULT_CHANNEL
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getChatMember",
            params={"chat_id": target_channel, "user_id": uid_int},
            timeout=8,
        )
        d = r.json()
    except Exception as e:
        return {"checked": False, "joined": None, "error": str(e)}

    if d.get("ok"):
        status = str((d.get("result") or {}).get("status", "")).lower()
        if status in JOINED_MEMBER_STATUSES:
            return {"checked": True, "joined": True, "status": status}
        if status in UNJOINED_MEMBER_STATUSES:
            return {"checked": True, "joined": False, "status": status}
        return {"checked": True, "joined": None, "status": status}

    desc = str(d.get("description", "") or "")
    desc_low = desc.lower()
    err_code = d.get("error_code")

    if err_code == 429:
        retry_after = int((d.get("parameters") or {}).get("retry_after", 5) or 5)
        return {"checked": False, "joined": None, "rate_limited": True, "retry_after": retry_after, "error": desc}

    fatal_markers = (
        "member list is inaccessible",
        "chat not found",
        "not enough rights",
        "bot is not a member",
        "chat_admin_required",
    )
    if any(m in desc_low for m in fatal_markers):
        return {"checked": False, "joined": None, "fatal_channel_error": True, "error": desc}

    if "user not found" in desc_low or "user_id_invalid" in desc_low or "participant_id_invalid" in desc_low:
        return {"checked": False, "joined": None, "skip_user": True, "error": desc}

    return {"checked": False, "joined": None, "error": desc}


def send_official_channel_reminder(user_id, bot_token=None, channel_handle=None, channel_url=None):
    """Send one gentle, non-compulsory reminder inviting the user to join the official channel."""
    token = (bot_token if bot_token is not None else os.getenv("BOT_TOKEN", "")).strip()
    if not token:
        return {"sent": False, "error": "BOT_TOKEN missing"}

    ch_handle = (channel_handle or DEFAULT_CHANNEL).strip() or DEFAULT_CHANNEL
    ch_url = (channel_url or OFFICIAL_CHANNEL_URL).strip() or "https://t.me/webtgfv1"

    msg_text = (
        "<b>Quick Reminder from WP Relay</b>\n\n"
        f"We post helpful automation tips, new features, and service updates inside our official channel <b>{ch_handle}</b>.\n\n"
        "Joining is completely optional — all bot features keep working either way — tap below whenever you'd like to follow updates!"
    )

    payload = {
        "chat_id": str(user_id).strip(),
        "text": msg_text,
        "parse_mode": "HTML",
        "disable_notification": True,
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "📢 Join Official Channel", "url": ch_url}],
                [{"text": "✅ I've Joined", "callback_data": "check_official_join"}],
            ]
        },
    }

    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=8)
        d = r.json()
    except Exception as e:
        return {"sent": False, "error": str(e)}

    if d.get("ok"):
        return {"sent": True}

    desc = str(d.get("description", "") or "")
    desc_low = desc.lower()
    err_code = d.get("error_code")

    if err_code == 403 or "blocked" in desc_low or "deactivated" in desc_low or "chat not found" in desc_low:
        return {"sent": False, "blocked": True, "error": desc}
    if err_code == 429:
        retry_after = int((d.get("parameters") or {}).get("retry_after", 5) or 5)
        return {"sent": False, "rate_limited": True, "retry_after": retry_after, "error": desc}
    return {"sent": False, "error": desc}


def run_official_channel_reminder_sweep(cooldown_seconds=REMINDER_COOLDOWN_SECONDS):
    """
    Check registered users against OFFICIAL_CHANNEL and gently remind unjoined users
    at most once every `cooldown_seconds` (48h default) until they join or block the bot.
    """
    if not _REMINDER_SWEEP_LOCK.acquire(blocking=False):
        return {"skipped": True, "reason": "sweep_already_running"}

    summary = {
        "skipped": False,
        "aborted": False,
        "abort_reason": "",
        "candidates": 0,
        "checked": 0,
        "already_joined": 0,
        "reminded": 0,
        "skipped_cooldown": 0,
        "blocked": 0,
        "errors": 0,
    }

    try:
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            summary["skipped"] = True
            summary["abort_reason"] = "BOT_TOKEN missing"
            return summary

        from database_manager import (
            get_feature_toggles,
            get_tenants,
            get_all_users,
            get_user_data,
            save_user_data,
        )

        toggles = get_feature_toggles() or {}
        if toggles.get("official_channel_reminders_enabled", True) is False:
            summary["skipped"] = True
            summary["abort_reason"] = "disabled_by_admin"
            return summary

        admin_id = str(os.getenv("ADMIN_ID", "5628105961")).strip()
        seen = set()
        candidates = []
        for raw_id in (get_tenants() or []) + (get_all_users() or []):
            uid = str(raw_id).strip()
            if not uid or uid == admin_id or uid in seen:
                continue
            seen.add(uid)
            candidates.append(uid)

        summary["candidates"] = len(candidates)
        now_ts = int(time.time())

        for uid in candidates:
            ud = get_user_data(uid, force_refresh=True) or {}
            if ud.get("bot_blocked"):
                summary["blocked"] += 1
                continue
            if ud.get("official_channel_joined"):
                summary["already_joined"] += 1
                continue

            res = check_user_channel_membership(uid, channel=DEFAULT_CHANNEL, bot_token=token)
            if res.get("rate_limited"):
                time.sleep(min(int(res.get("retry_after", 5)) + 1, 30))
                res = check_user_channel_membership(uid, channel=DEFAULT_CHANNEL, bot_token=token)

            if res.get("fatal_channel_error"):
                summary["aborted"] = True
                summary["abort_reason"] = res.get("error", "channel_check_failed")
                print(f"[CHANNEL REMINDER] Aborting sweep: {summary['abort_reason']}", flush=True)
                break

            if res.get("skip_user"):
                continue

            if not res.get("checked"):
                summary["errors"] += 1
                time.sleep(0.35)
                continue

            summary["checked"] += 1
            if res.get("joined") is True:
                ud["official_channel_joined"] = True
                ud["official_channel_checked_at"] = now_ts
                save_user_data(uid, ud)
                summary["already_joined"] += 1
                time.sleep(0.2)
                continue

            if res.get("joined") is False:
                ud["official_channel_joined"] = False
                ud["official_channel_checked_at"] = now_ts
                last_reminded = float(ud.get("official_channel_last_reminded_at") or 0)
                if (now_ts - last_reminded) < cooldown_seconds:
                    save_user_data(uid, ud)
                    summary["skipped_cooldown"] += 1
                    time.sleep(0.2)
                    continue

                send_res = send_official_channel_reminder(uid, bot_token=token)
                if send_res.get("rate_limited"):
                    time.sleep(min(int(send_res.get("retry_after", 5)) + 1, 30))
                    send_res = send_official_channel_reminder(uid, bot_token=token)

                if send_res.get("sent"):
                    ud["official_channel_last_reminded_at"] = now_ts
                    ud["official_channel_reminder_count"] = int(ud.get("official_channel_reminder_count") or 0) + 1
                    save_user_data(uid, ud)
                    summary["reminded"] += 1
                elif send_res.get("blocked"):
                    ud["bot_blocked"] = True
                    save_user_data(uid, ud)
                    summary["blocked"] += 1
                else:
                    save_user_data(uid, ud)
                    summary["errors"] += 1

            time.sleep(0.35)

        return summary
    except Exception as e:
        summary["aborted"] = True
        summary["abort_reason"] = str(e)
        print(f"[CHANNEL REMINDER ERROR] {e}", flush=True)
        return summary
    finally:
        _REMINDER_SWEEP_LOCK.release()
