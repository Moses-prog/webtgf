import os
import json
import time
import requests
from dotenv import load_dotenv, set_key

load_dotenv()

DEFAULT_CHANNEL = "@webtgfv1"
DEFAULT_BOT_USERNAME = "wprelaybot"

# Knowledge Base & System Manifesto for WP Relay
WP_RELAY_KNOWLEDGE = """
You are the Official Lead Engineer and Growth Strategist for WP Relay (@wprelaybot), the enterprise Telegram channel forwarding, rewriting, and automation bot.
Official Channel: @webtgfv1
Bot: @wprelaybot

WP RELAY CAPABILITIES & CORE FEATURES:
1. Anti-Ban Human Simulation & Jitter Delay:
   - Configurable randomized delay (e.g. 5s - 45s) between source capture and target delivery.
   - Prevents Telegram FloodWait errors, spam detection, and channel bans.

2. Global Link & Username Rewriting (Global Swaps):
   - Automatically detects ANY competitor t.me link or website link and swaps it to the tenant's own channel or affiliate URL.
   - Automatically finds competitor @mentions and swaps them to the tenant's own handle.
   - Custom regex word replacements and keyword filtering.

3. Dynamic Image Watermarking Engine:
   - Stretches or stamps custom text/logo watermarks on forwarded media.
   - Complete brand protection: removes competitor branding by overriding with custom watermark.

4. Media & Video Swap:
   - Replaces source channel video clips or banners with custom high-converting promo videos or pictures.

5. Interactive Call-To-Action (CTA) Inline Buttons:
   - Appends native Telegram inline buttons (e.g. [ ⚡ Join VIP ], [ 💎 Claim Bonus ], [ 🚀 Start Trading ]) directly below forwarded posts.

6. Drip Posting Pacer:
   - When a source channel posts 15 messages in 2 minutes, WP Relay queues and drips them smoothly (e.g. 1 post every 3 minutes) so followers don't mute or leave.

7. Smart Sleep Schedule:
   - Automatically pauses forwarding during night hours (e.g. 11 PM to 7 AM) and resumes in the morning to protect subscriber sleep cycles.

8. Auto-Delete & Ephemeral Drops (Rolling Message Limits):
   - Auto-deletes forwarded posts after X hours (ideal for timed signals, flash deals, VIP previews).
   - Rolling limits keep channel history clean and exclusive.

9. Mirror Deletion & Synchronized Editing:
   - If a source admin edits a typo or deletes a post, WP Relay instantly mirrors the edit/delete in target channels.

10. Coming Soon:
   - WP Studio: Automated AI creative banner generator and video styler.
   - WP Assistant: Autonomous AI Telegram community moderator and conversational admin.
"""

TOPIC_CATEGORIES = [
    {
        "id": "anti_ban",
        "title": "Anti-Ban & Human Simulation",
        "prompt": "Write a high-impact channel tip on how Telegram channel owners can avoid spam flags and account bans by using WP Relay's intelligent Human Simulation Jitter Delay. Explain why instant zero-second forwarding triggers Telegram flood limits and how human jitter protects the channel."
    },
    {
        "id": "link_rewriting",
        "title": "Automated Link & Mention Monetization",
        "prompt": "Write an actionable guide on how to automatically monetize forwarded content using WP Relay's Global Link & Username Rewriting engine. Explain how to instantly hijack competitor traffic by replacing all incoming links and @mentions with your own affiliate links and channel handles."
    },
    {
        "id": "watermarking",
        "title": "Dynamic Watermarking & Brand Defense",
        "prompt": "Write an engaging post on brand protection using WP Relay's Dynamic Watermark Engine. Explain how channel admins can prevent content theft and establish authority by auto-stamping their custom watermark on every forwarded photo."
    },
    {
        "id": "cta_buttons",
        "title": "High-Converting CTA Inline Buttons",
        "prompt": "Write a growth hack tip on boosting channel conversions by 300% using WP Relay's Native Telegram Inline CTA Buttons. Explain how adding clickable buttons below every forwarded message drives immediate traffic to VIP bots or affiliate signups."
    },
    {
        "id": "drip_pacer",
        "title": "Drip Posting Pacer vs Audience Churn",
        "prompt": "Write a masterclass tip on channel retention: Why spamming 20 posts at once kills follower retention, and how WP Relay's Drip Posting Pacer queues and spaces posts evenly throughout the day to keep subscribers active without muting."
    },
    {
        "id": "auto_delete",
        "title": "Ephemeral Content & Auto-Delete Cleanups",
        "prompt": "Write a post on how premium signal channels and VIP clubs use WP Relay's Auto-Delete rolling timers to create FOMO, protect proprietary content, and keep target channels clean and clutter-free."
    },
    {
        "id": "pro_features",
        "title": "WP Relay PRO Power Suite",
        "prompt": "Write an exciting spotlight on why serious channel owners upgrade to WP Relay PRO: unlimited channel routes, custom video overrides, priority high-speed worker threads, and dynamic watermarks."
    },
    {
        "id": "telegram_growth",
        "title": "Multi-Channel Growth Strategy",
        "prompt": "Write an insider strategy guide on scaling a Telegram network across 10+ niche channels simultaneously using WP Relay's multi-source to multi-target routing matrix with zero manual forwarding."
    }
]

AUTOPILOT_FILE = "channel_autopilot.json"

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
        instruction = f"Topic to write about: {custom_prompt}"
    elif chosen_category:
        instruction = chosen_category["prompt"]
    else:
        # Fallback to random or first
        import random
        cat = random.choice(TOPIC_CATEGORIES)
        instruction = cat["prompt"]

    system_prompt = f"""
{WP_RELAY_KNOWLEDGE}

TASK:
Write an extremely smart, polished, and compelling Telegram channel broadcast post for our official channel: @webtgfv1.
Instructions:
- Topic: {instruction}
- Visual Style: Use rich, classy emojis (⚡, 🛡️, 💎, 📌, 🚀, 💡, ⚙️, 🎯).
- Format: Telegram HTML (use <b>bold</b>, <i>italic</i>, <code>code</code>, bullet points).
- Structure:
  1. Catchy headline with emojis (e.g. ⚡ <b>WP RELAY PRO TIP: ...</b>)
  2. The Challenge/Insight: Why this matters to channel growth, security, or monetization.
  3. The Actionable Technique / Solution: Clear step-by-step or breakdown.
  4. Quick Takeaway: 1-2 punchy summary lines.
  5. Call to Action: Invite the reader to tap the buttons below to launch or upgrade @wprelaybot.
- Output ONLY the post text itself. Do not include introductory notes or markdown codeblocks (no ```html).
"""

    models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]
    last_err = None

    for m in models_to_try:
        try:
            resp = client.models.generate_content(
                model=m,
                contents=system_prompt
            )
            if resp and resp.text:
                text = resp.text.strip()
                # Clean any markdown code ticks if wrapped
                if text.startswith("```html"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

                recommended_buttons = [
                    {"text": "⚡ Launch WP Relay Bot", "url": "https://t.me/wprelaybot?start=channel_tip"},
                    {"text": "💎 Upgrade to PRO", "url": "https://t.me/wprelaybot?start=pro_upgrade"}
                ]
                return {
                    "text": text,
                    "buttons": recommended_buttons,
                    "model_used": m
                }
        except Exception as e:
            last_err = e

    raise RuntimeError(f"All Gemini models failed: {last_err}")

def publish_to_channel(text, buttons=None, pin=False, target_channel=DEFAULT_CHANNEL, disable_notification=False):
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is not configured in .env.")

    if not target_channel:
        target_channel = DEFAULT_CHANNEL

    # Clean channel format
    target_channel = target_channel.strip()
    if not target_channel.startswith("@") and not target_channel.startswith("-100") and not target_channel.isdigit():
        target_channel = "@" + target_channel

    payload = {
        "chat_id": target_channel,
        "text": text,
        "parse_mode": "HTML",
        "disable_notification": bool(disable_notification)
    }

    if buttons and isinstance(buttons, list) and len(buttons) > 0:
        inline_keyboard = []
        row = []
        for btn in buttons:
            txt = btn.get("text", "").strip()
            url = btn.get("url", "").strip()
            if txt and url:
                if not url.startswith(("http://", "https://", "t.me/")):
                    url = "https://" + url
                row.append({"text": txt, "url": url})
                if len(row) >= 2:
                    inline_keyboard.append(row)
                    row = []
        if row:
            inline_keyboard.append(row)
        
        if inline_keyboard:
            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

    # Send Message
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=12)
    res_data = r.json()

    if not res_data.get("ok"):
        desc = res_data.get("description", "Unknown Telegram error")
        code = res_data.get("error_code")
        if code == 401:
            raise RuntimeError(f"Telegram Bot Token is unauthorized. Please verify the BOT_TOKEN in Admin Settings.")
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
            pinned = pin_data.get("ok", False)
        except Exception as e:
            print(f"[PIN ERROR] Failed to pin message {msg_id}: {e}")

    # Record history in autopilot
    try:
        cfg = get_autopilot_config()
        cfg["last_posted_at"] = int(time.time())
        snippet = text[:120].replace("\n", " ") + "..."
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

def run_autopilot_tick():
    cfg = get_autopilot_config()
    if not cfg.get("enabled", False):
        return None

    freq_hours = max(1, int(cfg.get("frequency_hours", 12)))
    interval_sec = freq_hours * 3600
    now = int(time.time())
    last_run = int(cfg.get("last_posted_at", 0))

    if now - last_run < interval_sec:
        # Not time yet
        return None

    # Time to post!
    idx = cfg.get("topic_index", 0) % len(TOPIC_CATEGORIES)
    category = TOPIC_CATEGORIES[idx]

    try:
        print(f"[AUTOPILOT] Generating scheduled post for category '{category['id']}'...")
        post_data = generate_channel_post(category_id=category["id"])
        
        # Determine if this tip should be pinned (e.g. anti-ban or pro guide)
        should_pin = category["id"] in ["anti_ban", "pro_features"]

        result = publish_to_channel(
            text=post_data["text"],
            buttons=post_data["buttons"],
            pin=should_pin,
            target_channel=DEFAULT_CHANNEL
        )
        print(f"[AUTOPILOT] Successfully published scheduled post: {result}")

        # Advance topic index
        cfg["topic_index"] = (idx + 1) % len(TOPIC_CATEGORIES)
        cfg["last_posted_at"] = now
        save_autopilot_config(cfg)
        return result
    except Exception as e:
        print(f"[AUTOPILOT] Scheduled post error: {e}")
        return None
