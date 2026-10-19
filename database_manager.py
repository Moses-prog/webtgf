import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def send_telegram_alert(chat_id, text, button_text="💎 RENEW PRO ACCESS ↗", button_url="https://t.me/apklord55"):
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token or not chat_id:
        return False
    import requests
    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "parse_mode": "HTML"
    }
    if button_text and button_url:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [{"text": button_text, "url": button_url}]
            ]
        }
    try:
        r = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json=payload, timeout=8)
        return bool(r.status_code == 200)
    except Exception as e:
        print(f"[ALERT ERROR] Failed to send Telegram alert to {chat_id}: {e}")
        return False

def get_user_data(chat_id):
    """Returns the user's config dict from Supabase, or a default template if they don't exist."""
    chat_id = str(chat_id)
    default_data = {
        "api_id": "",
        "api_hash": "",
        "session_string": "",
        "sources": [],
        "targets": [],
        "text_swaps": {},
        "image_swap_url": "",
        "image_swap_path": "",
        "replace_all_links_with": "",
        "replace_all_usernames_with": "",
        "is_active": False
    }
    
    if not supabase:
        print("WARNING: Supabase not configured!")
        return default_data
        
    try:
        response = supabase.table('users').select('data').eq('chat_id', chat_id).execute()
        if response.data and len(response.data) > 0:
            # Merge with default to ensure keys exist
            data = {**default_data, **response.data[0]['data']}
            
            # Check PRO Expiry
            if data.get('is_pro') and data.get('pro_expiry'):
                import datetime
                try:
                    expiry = datetime.datetime.fromisoformat(data['pro_expiry'])
                    now = datetime.datetime.now()
                    
                    # 1. Check if expired
                    if now > expiry:
                        data['is_pro'] = False
                        data['pro_expired_at'] = data.get('pro_expiry')
                        data['pro_paused'] = True
                        if not data.get('expiry_notified'):
                            data['expiry_notified'] = True
                            expires_str = str(data.get('pro_expiry'))[:16]
                            alert_text = (
                                "🚨 <b>WP RELAY: PRO SUBSCRIPTION EXPIRED</b>\n\n"
                                f"Dear Subscriber,\nYour PRO plan for account <code>{chat_id}</code> expired on <b>{expires_str}</b>.\n\n"
                                "⛔ <b>ALL CHANNEL FORWARDING & FEATURES HAVE BEEN PAUSED.</b>\n"
                                "Your destination channels will no longer receive any forwarded messages or updates until you renew.\n\n"
                                "• 🔴 Auto-Forwarding: <b>PAUSED</b>\n"
                                "• 🔴 Anti-Ban Human Jitter: <b>PAUSED</b>\n"
                                "• 🔴 Custom Watermarks & Media Swapping: <b>PAUSED</b>\n"
                                "• 🔴 High-Converting CTA Buttons: <b>PAUSED</b>\n\n"
                                "👉 <i>Renew now with Administrator @apklord55 to unpause your channels immediately.</i>"
                            )
                            send_telegram_alert(chat_id, alert_text, "💎 RENEW PRO ACCESS (UNPAUSE) ↗", "https://t.me/apklord55")
                        save_user_data(chat_id, data)
                        
                    # 2. Check 24-hour advance warning
                    elif 0 < (expiry - now).total_seconds() <= 86400:
                        if not data.get('expiry_warning_24h_notified'):
                            data['expiry_warning_24h_notified'] = True
                            expires_str = str(data.get('pro_expiry'))[:16]
                            hours_left = max(1, int((expiry - now).total_seconds() // 3600))
                            alert_text = (
                                "⏳ <b>WP RELAY: 24-HOUR PRO EXPIRATION NOTICE</b>\n\n"
                                f"Your PRO plan will expire in <b>{hours_left} hours</b> (<code>{expires_str}</code>).\n\n"
                                "⚠️ <b>CRITICAL WARNING:</b> The moment your plan expires, <b>all channel relays and automation features will be immediately PAUSED</b>.\n\n"
                                "To maintain 100% continuous uptime across your channels, please contact Administrator @apklord55 to extend your license now."
                            )
                            send_telegram_alert(chat_id, alert_text, "⚡ EXTEND PRO NOW (PREVENT PAUSE) ↗", "https://t.me/apklord55")
                            save_user_data(chat_id, data)
                except Exception as ex_err:
                    print(f"[PRO CHECK ERROR] {ex_err}")
                
            return data
        else:
            return default_data
    except Exception as e:
        print(f"Supabase read error: {e}")
        return default_data

def save_user_data(chat_id, data):
    chat_id = str(chat_id)
    if not supabase:
        print("WARNING: Supabase not configured!")
        return
        
    try:
        supabase.table('users').upsert({"chat_id": chat_id, "data": data}).execute()
    except Exception as e:
        print(f"Supabase write error: {e}")

def get_all_users():
    """Returns a list of all chat_ids that have configurations in Supabase."""
    if not supabase:
        return []
        
    try:
        response = supabase.table('users').select('chat_id').execute()
        return [row['chat_id'] for row in response.data]
    except Exception as e:
        print(f"Supabase get_all_users error: {e}")
        return []

def get_tenants():
    if not supabase: return []
    try:
        response = supabase.table('platform_state').select('value').eq('key', 'tenants').execute()
        return response.data[0]['value'] if response.data else []
    except:
        return []

def save_tenants(tenants):
    if not supabase: return
    try:
        supabase.table('platform_state').upsert({'key': 'tenants', 'value': tenants}).execute()
    except: pass

def get_stats():
    if not supabase: return {'total': 0, 'today': 0, 'date': ''}
    try:
        response = supabase.table('platform_state').select('value').eq('key', 'stats').execute()
        return response.data[0]['value'] if response.data else {'total': 0, 'today': 0, 'date': ''}
    except:
        return {'total': 0, 'today': 0, 'date': ''}

def save_stats(stats):
    if not supabase: return
    try:
        supabase.table('platform_state').upsert({'key': 'stats', 'value': stats}).execute()
    except: pass
def get_feature_toggles():
    if not supabase: return {}
    try:
        response = supabase.table('platform_state').select('value').eq('key', 'toggles').execute()
        return response.data[0]['value'] if response.data else {}
    except:
        return {}

def save_feature_toggles(toggles):
    if not supabase: return
    try:
        supabase.table('platform_state').upsert({'key': 'toggles', 'value': toggles}).execute()
    except: pass


def save_message_map(tenant_id, source_chat, source_msg, target_chat, target_msg):
    if not supabase: return
    try:
        data = {
            "tenant_id": str(tenant_id),
            "source_channel_id": str(source_chat).replace("-100", "").replace("-", ""),
            "source_msg_id": str(source_msg),
            "target_channel_id": str(target_chat),
            "target_msg_id": str(target_msg)
        }
        supabase.table("message_map").insert(data).execute()
    except Exception as e:
        print(f"Error saving message map: {e}")

def get_target_messages(tenant_id, source_chat, source_msg):
    if not supabase: return []
    try:
        source_clean = str(source_chat).replace("-100", "").replace("-", "")
        response = supabase.table("message_map").select("target_channel_id, target_msg_id").eq("tenant_id", str(tenant_id)).eq("source_channel_id", source_clean).eq("source_msg_id", str(source_msg)).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting target messages: {e}")
        return []

def cleanup_message_map():
    if not supabase: return
    try:
        # Delete messages older than 30 days
        import datetime
        thirty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        supabase.table("message_map").delete().lt("created_at", thirty_days_ago).execute()
    except:
        pass
