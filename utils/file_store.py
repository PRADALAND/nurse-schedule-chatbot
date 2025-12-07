# utils/file_store.py
import time
from utils.supabase_client import get_supabase_client

BUCKET = "chatbot-files"

def _safe_filename(user_id: str, original: str) -> str:
    ts = int(time.time())
    return f"{user_id}/{ts}_{original}"

def upload_file(user_id: str, file_obj):
    """
    Streamlit UploadedFile → Supabase Storage 업로드 후
    (path, public_url) 반환.
    """
    sb = get_supabase_client()

    file_bytes = file_obj.read()
    path = _safe_filename(user_id, file_obj.name)

    sb.storage.from_(BUCKET).upload(
        path,
        file_bytes,
        {"content-type": file_obj.type},
    )

    public_url = sb.storage.from_(BUCKET).get_public_url(path)
    return path, public_url
