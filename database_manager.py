import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

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
            return {**default_data, **response.data[0]['data']}
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
