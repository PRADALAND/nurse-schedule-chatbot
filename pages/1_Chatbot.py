import streamlit as st
import requests
import os

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = os.getenv("HF_API_URL")
HF_MODEL = os.getenv("HF_MODEL")

# ------------------------------
# LLM 호출 함수
# ------------------------------
def call_llm(prompt: str) -> str:
    if not HF_API_TOKEN:
        return "❌ HF_API_TOKEN이 설정되지 않았습니다."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.3
        }
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload)
        
        # Unauthorized 체크
        if resp.status_code == 401:
            return "❌ Unauthorized: HF API 토큰 권한을 다시 확인하세요."

        data = resp.json()

        # Mistral 형태 파싱
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]

        # 오류 반환
        return f"❌ 모델 응답 파싱 실패 → {data}"

    except Exception as e:
        return f"❌ 호출 오류: {e}"


# ------------------------------
# Streamlit UI
# ------------------------------
def main():
    st.title("근무 스케줄 챗봇 (AI 기반)")

    query = st.text_input("질문을 입력하세요.")
    
    if st.button("질문 보내기") and query.strip():
        answer = call_llm(query)
        st.markdown(f"**AI:** {answer}")


if __name__ == "__main__":
    main()
