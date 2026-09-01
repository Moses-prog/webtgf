with open('database_manager.py', 'a', encoding='utf-8') as f:
    f.write('''

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
''')
print('Added message map functions to database_manager.py')
