from .supabase_client import get_supabase

TABLE = "analysis_logs"

def log_analysis(user_id, file_name, file_type, file_url, user_prompt, ai_summary):
    sb = get_supabase()
    sb.table(TABLE).insert({
        "user_id": user_id,
        "file_name": file_name,
        "file_type": file_type,
        "file_url": file_url,
        "user_prompt": user_prompt,
        "ai_summary": ai_summary,
    }).execute()

def fetch_logs(limit=200):
    sb = get_supabase()
    res = sb.table(TABLE).select("*").order("created_at", desc=True).limit(limit).execute()
    return res.data

