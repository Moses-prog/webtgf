import os
import json
import time
import re
import random
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CHANNEL = "@webtgfv1"
DEFAULT_BOT_USERNAME = "wprelaybot"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOPILOT_FILE = os.path.join(BASE_DIR, "channel_autopilot.json")
LOCK_FILE = os.path.join(BASE_DIR, "autopilot.lock")

# Enterprise Knowledge Base for WP Relay Automation
WP_RELAY_KNOWLEDGE = """
You are the Growth Architect & Principal Automation Engineer for WP Relay (@wprelaybot), the enterprise Telegram channel forwarding, rewriting, and stealth automation system.
Official Channel: @webtgfv1
Bot Handle: @wprelaybot

WP RELAY CORE CAPABILITIES:
1. Anti-Ban Human Jitter Delay: Randomized delivery pause (8s-35s) mimicking organic human reading and posting, completely evading Telegram's FloodWait locks and spam heuristics.
2. Global Link & Username Rewriter: Auto-detects and swaps any competitor t.me links, external websites, or @mentions with the tenant's own handle, referral links, and affiliate URLs.
3. Dynamic Watermark Engine: Auto-stamps custom brand text, logos, or channel usernames directly onto forwarded photos and graphics.
4. Interactive CTA Conversion Buttons: Appends high-converting clickable inline buttons (with custom labels, deep links, and color styles) directly below forwarded drops.
5. Drip Posting Pacer: Buffers rapid-fire drops from high-volume source channels and spaces them out smoothly over minutes or hours so subscribers never mute the channel.
6. Ephemeral Auto-Delete Timers: Automatically purges posts after X hours (e.g. 2h, 6h, 12h, 24h), creating VIP urgency, FOMO, and protecting proprietary trade/signal drops from leaking.
7. Real-Time Mirror Deletion & Live Sync: Instantly mirrors edits, text corrections, and message deletions made in source channels across all destinations.
8. Multi-Channel Syndication: Routes content from a single master source into 10+ niche target channels simultaneously with custom per-channel rewriting rules.
9. PRO High-Velocity Workers: Dedicated worker threads with sub-second execution, custom video overrides, and unlimited forward routing.
"""

STRATEGIC_PILLARS = [
    {
        "id": "anti_ban",
        "title": "Anti-Ban & Stealth Jitter",
        "description": "How 0-second bot forwarding gets accounts flagged by Telegram heuristics, and how WP Relay's 8-35s randomized human jitter creates 100% undetected stealth delivery."
    },
    {
        "id": "link_rewriting",
        "title": "Link Arbitrage & Competitor Poaching",
        "description": "Automated monetization: replacing competitor affiliate links, tracking URLs, and usernames with the operator's own handles without editing a single post manually."
    },
    {
        "id": "auto_delete",
        "title": "Ephemeral Drops & VIP Scarcity",
        "description": "Using auto-delete timers (2h, 6h, 12h) to drive insane open rates, trigger subscriber FOMO, and keep premium signal feeds spotless."
    },
    {
        "id": "watermarking",
        "title": "Dynamic Watermarking & Brand Defense",
        "description": "Auto-stamping custom branding or channel usernames onto forwarded images to prevent competitor scraping and claim visual ownership."
    },
    {
        "id": "drip_pacer",
        "title": "Drip Pacing & Feed Hygiene",
        "description": "Why forward dumping 20 posts at once spikes subscriber mutes by 70%, and how WP Relay's Drip Pacer queues and spaces content smoothly."
    },
    {
        "id": "cta_buttons",
        "title": "Interactive CTA Conversion Funnels",
        "description": "How adding native styled inline buttons beneath every drop turns passive viewers into VIP bot users and paying customers."
    },
    {
        "id": "multi_channel",
        "title": "Multi-Channel Syndication Network",
        "description": "Scaling 1 source channel into a 10-channel niche media empire automatically with independent routing rules per channel."
    },
    {
        "id": "live_sync",
        "title": "Live Message Sync & Mirror Deletion",
        "description": "Fixing typos or deleting retracted source alerts across all forward destinations in real-time with zero lag."
    },
    {
        "id": "algo_hacks",
        "title": "Telegram Search & Discovery Algorithms",
        "description": "How post engagement velocity, instant reactions, and keyword pinning skyrocket Telegram global search ranking."
    },
    {
        "id": "pro_workers",
        "title": "PRO Concurrency & Enterprise Infrastructure",
        "description": "Why high-scale Telegram operators run dedicated worker processes to handle 50,000+ daily forwards without dropping messages."
    },
    {
        "id": "case_study",
        "title": "Real Operator Case Study",
        "description": "Concrete breakdown of how a niche channel operator scaled views, unmuted rates, or affiliate revenue using WP Relay automation."
    },
    {
        "id": "myth_busters",
        "title": "Telegram Growth Myths Debunked",
        "description": "Exposing the fatal mistakes 95% of channel creators make when copying content or managing forward channels."
    }
]

# Keep TOPIC_CATEGORIES as an alias for backwards compatibility with web API & Mini App UI
TOPIC_CATEGORIES = STRATEGIC_PILLARS

EDITORIAL_FORMATS = [
    {
        "id": "case_study",
        "name": "Micro Case Study",
        "instruction": """
Format as a crisp REAL-WORLD OPERATOR CASE STUDY:
- Header: 📊 <b>CASE STUDY: [Punchy 3-5 Word Scenario]</b>
- The Setup: 1 sentence introducing a specific channel type (e.g. 35k crypto channel or sports signals) and their exact bottleneck.
- The Pivot: How they deployed a specific WP Relay feature to solve it.
- The Numbers: Concrete result (e.g., +44% unmuted views, $1.8k monthly affiliate lift, 0 shadowbans).
- The Takeaway / CTA: 1 sharp sentence pointing to @wprelaybot.
"""
    },
    {
        "id": "myth_buster",
        "name": "Unpopular Truth / Myth Buster",
        "instruction": """
Format as a contrarian UNPOPULAR TRUTH / MYTH BUSTER:
- Header: ⚡ <b>UNPOPULAR TRUTH: [Bold Contrarian Statement]</b>
- The Myth: What 90% of Telegram channel owners mistakenly believe.
- The Reality: What Telegram's actual algorithms or user behavior do instead.
- The Smart Move: How WP Relay handles this with mathematical precision.
- The Takeaway / CTA: 1 punchy sentence pointing to @wprelaybot.
"""
    },
    {
        "id": "stealth_playbook",
        "name": "3-Step Stealth Playbook",
        "instruction": """
Format as a tactical 3-STEP STEALTH PLAYBOOK:
- Header: 🛡️ <b>PLAYBOOK: [Action-Oriented Goal in 3-5 Words]</b>
- The Objective: 1 punchy line explaining the strategy.
- 3 Clear Steps:
  • <b>Step 1:</b> [Tactical action]
  • <b>Step 2:</b> [Tactical action]
  • <b>Step 3:</b> [Tactical action]
- Pro Tip: 1 sentence tactical secret.
- The Takeaway / CTA: 1 sharp sentence pointing to @wprelaybot.
"""
    },
    {
        "id": "security_alert",
        "name": "Security & Risk Briefing",
        "instruction": """
Format as an urgent SECURITY & RISK BRIEFING:
- Header: 🚨 <b>SECURITY BRIEFING: [Specific Threat or Trigger]</b>
- The Risk: What heuristic Telegram's automated spam detection flags (e.g. FloodWait, 0s bursts).
- The Vulnerability: Why raw or manual forwarding gets channels shadowbanned or locked.
- The Immunity Protocol: How WP Relay's engineering provides 100% stealth protection.
- The Takeaway / CTA: 1 urgent sentence pointing to @wprelaybot.
"""
    },
    {
        "id": "growth_teardown",
        "name": "Operator Growth Teardown",
        "instruction": """
Format as a high-level OPERATOR GROWTH TEARDOWN:
- Header: 💡 <b>GROWTH TEARDOWN: [The Strategic Lever in 3-5 Words]</b>
- The Problem: The friction keeping 99% of Telegram channels small or unmonetized.
- The Architecture: How top networks stack automation (rewriting + pacing + CTA buttons).
- The ROI: The massive compounding advantage of hands-off automation.
- The Takeaway / CTA: 1 punchy sentence pointing to @wprelaybot.
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

OBJECTIVE:
Generate an ultra-engaging, high-value Telegram channel post for @webtgfv1 that provides actionable insider value to channel owners.

TARGET STRATEGIC PILLAR:
"{pillar_title}": {pillar_topic}

EDITORIAL FORMAT TO USE:
{chosen_format["instruction"]}

{recent_history_context}

CRITICAL RULES:
1. WORD COUNT: 75 to 95 WORDS TOTAL.
2. STRICT POST ALIGNMENT (MUST FOLLOW THIS EXACT FIXED STRUCTURE):
⚡ <b>WP RELAY: [Punchy 3-5 Word Title]</b>

<i>[One sharp sentence explaining the challenge or angle]</i>

• 🚨 <b>The Bottleneck:</b> [1 punchy sentence]
• 🛡️ <b>The Architecture:</b> [1 punchy sentence explaining the WP Relay feature]
• 💎 <b>The Advantage:</b> [1 punchy sentence on the measurable win]

👉 <i>Configure in 30 seconds inside @wprelaybot:</i>

3. ALLOWED HTML TAGS: <b>, <i>, <code>, <s>, <u>, <a href="...">, <tg-spoiler>.
   DO NOT use <ul>, <ol>, <li>, <p>, <div>, or markdown.
4. DYNAMIC THEME PAIRING: Choose the most fitting visual theme:
   - "cyber_cyan": For stealth, pacing, tech automation, or core features.
   - "crimson_alert": For security alerts, anti-ban warnings, or risk briefings.
   - "emerald_cash": For monetization, affiliate link arbitrage, or revenue scaling.
   - "royal_purple": For PRO features, VIP masterclass, or enterprise scaling.
   - "sunset_amber": For viral hacks, growth velocity, algorithm tricks, or high engagement.
   - "stealth_mono": For minimal enterprise, multi-channel syndication, or infrastructure.
5. BUTTONS: Provide 2 full-width inline buttons with clear labels:
   Button 1: {{"text": "⭐ LAUNCH WP RELAY BOT ⚡", "url": "https://t.me/wprelaybot?start=channel_tip", "style": "primary"}}
   Button 2: {{"text": "💎 UPGRADE TO PRO (VIP) ✅", "url": "https://t.me/wprelaybot?start=pro_upgrade", "style": "success"}}

OUTPUT FORMAT:
You MUST output a strict JSON object with these EXACT keys:
{{
  "card_title": "PUNCHY 2-4 WORD CARD HEADLINE (UPPERCASE)",
  "card_subtitle": "COMPELLING 6-9 WORD VALUE HOOK (UPPERCASE)",
  "category_badge": "2-3 WORD BADGE (e.g. SECURITY ALERT, CASE STUDY, GROWTH HACK, OPERATOR PLAYBOOK)",
  "theme": "one of: cyber_cyan, crimson_alert, emerald_cash, royal_purple, sunset_amber, stealth_mono",
  "feature_pills": ["PILL 1", "PILL 2", "PILL 3"],
  "should_pin": false,
  "text": "Full Telegram post text with bold HTML and natural formatting",
  "buttons": [
    {{"text": "BUTTON 1 LABEL (E.G. 🛡️ ENABLE BAN SHIELD)", "url": "https://t.me/wprelaybot?start=topic_slug", "style": "primary"}},
    {{"text": "BUTTON 2 LABEL (E.G. ⚡ LAUNCH @WPRELAYBOT)", "url": "https://t.me/wprelaybot?start=main", "style": "success"}}
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
                card_title = parsed.get("card_title", "WP RELAY PRO").strip()
                card_subtitle = parsed.get("card_subtitle", "SMART TELEGRAM CHANNEL AUTOMATION").strip()
                category_badge = parsed.get("category_badge", chosen_format["name"]).strip()
                theme = parsed.get("theme", "cyber_cyan").strip()
                feature_pills = parsed.get("feature_pills", ["100% STEALTH", "SMART PACER", "BAN-PROOF"])
                should_pin = bool(parsed.get("should_pin", False))

                buttons = parsed.get("buttons") or [
                    {"text": "⭐ LAUNCH WP RELAY BOT ⚡", "url": "https://t.me/wprelaybot?start=channel_tip", "style": "primary"},
                    {"text": "💎 UPGRADE TO PRO (VIP) ✅", "url": "https://t.me/wprelaybot?start=pro_upgrade", "style": "success"}
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
