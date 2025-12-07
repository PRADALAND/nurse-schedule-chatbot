import time
from .supabase_client import get_supabase

BUCKET = "chatbot-files"

def upload_file(user_id: str, file_obj):
    sb = get_supabase()
    filename = f"{user_id}/{int(time.time())}_{file_obj.name}"
    content = file_obj.read()

    sb.storage.from_(BUCKET).upload(filename, content, {
        "content-type": file_obj.type
    })

    url = sb.storage.from_(BUCKET).get_public_url(filename)
    return filename, url

