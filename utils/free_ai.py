import requests
import streamlit as st

# 1) Streamlit secrets에서 직접 읽기
HF_API_TOKEN = st.secrets.get("HF_API_TOKEN", None)
HF_API_URL = st.secrets.get("HF_API_URL", None)
HF_MODEL = st.secrets.get("HF_MODEL", None)

def call_llm(prompt: str) -> str:
    if HF_API_TOKEN is None:
        return "ERROR: HF_API_TOKEN이 없습니다. Streamlit secrets.toml을 확인하세요."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 256,
            "temperature": 0.4
        }
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
    except Exception as e:
        return f"HF 호출 실패: {e}"

    # JSON parsing
    try:
        data = resp.json()
    except Exception:
        return f"(HF 응답 JSON 파싱 실패) status={resp.status_code}, text={resp.text}"

    # Authorization 실패한 경우
    if resp.status_code == 401:
        return f"Unauthorized: 토큰이 잘못됐거나 Streamlit secrets에서 읽히지 않았습니다. data={data}"

    if "error" in data:
        return f"(HF API 오류) {data['error']}"

    # zephyr 구조
    if isinstance(data, list) and "generated_text" in data[0]:
        return data[0]["generated_text"]

    return f"(파싱 실패) 원본={data}"
