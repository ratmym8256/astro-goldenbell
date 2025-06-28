import streamlit as st
import pdfplumber
import random
import re

PDF_PATH = "도전골든벨_어린이천문대_2025.pdf"

# PDF에서 문제 추출하는 함수
def extract_quiz_from_pdf(pdf_path):
    quiz_list = []
    level_map = {
        "난이도 하": "하",
        "난이도 중": "중",
        "난이도 상": "상",
        "난이도 최상": "최상"
    }
    current_level = None
    question_pattern = re.compile(r"^\d+\.\s*(.+?)(?:정답\s*:\s*|$)")
    answer_pattern = re.compile(r"정답\s*:\s*([^\n]+)")
    
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    lines = text.split("\n")
    for line in lines:
        for key, val in level_map.items():
            if key in line:
                current_level = val
        if re.match(r"^\d+\.", line) and current_level:
            q = question_pattern.search(line)
            a = answer_pattern.search(line)
            if q and a:
                quiz_list.append({
                    "level": current_level,
                    "question": q.group(1).strip(),
                    "answer": a.group(1).strip()
                })
    return quiz_list

@st.cache_data
def load_quiz():
    return extract_quiz_from_pdf(PDF_PATH)

quiz_bank = load_quiz()
levels = ["하", "중", "상", "최상"]

# 제목과 안내
st.title("🎉 도전! 골든벨 퀴즈 놀이방")
st.write("원하는 난이도를 고르고, 문제를 풀어보세요! 궁금한 문제는 소리로도 들을 수 있어요!")

# 난이도 안내
st.markdown("#### 난이도를 골라 주세요!")
level = st.radio("", levels, horizontal=True, captions=["쉬움", "보통", "조금 어려움", "진짜 어려움"])

filtered = [q for q in quiz_bank if q["level"] == level]

# 상태 초기화
if "current_q" not in st.session_state:
    st.session_state.current_q = None
    st.session_state.show_a = False

col1, col2 = st.columns(2)

# 버튼 및 상태 변경
with col1:
    if st.button("🧩 새로운 문제 나와라!"):
        st.session_state.current_q = random.choice(filtered) if filtered else None
        st.session_state.show_a = False

with col2:
    if st.button("✨ 정답 알려줘!"):
        st.session_state.show_a = True

# 문제, 음성 버튼
if st.session_state.current_q:
    st.info("🔔 문제: " + st.session_state.current_q["question"])

    # "음성으로 들려줘!" 버튼 (모바일, PC 모두에서 동작)
    st.components.v1.html(f"""
        <button onclick="var utter=new window.SpeechSynthesisUtterance('{st.session_state.current_q["question"].replace("'", "")}'); utter.lang='ko-KR'; utter.rate=1.0; window.speechSynthesis.cancel(); window.speechSynthesis.speak(utter);" style="font-size:18px;padding:8px 20px;border-radius:12px;background:#ffd700;border:none;cursor:pointer;margin-bottom:8px;">
            🔊 음성으로 들려줘!
        </button>
    """, height=60)

    if st.session_state.show_a:
        st.success("🎯 정답: " + st.session_state.current_q["answer"])
elif not filtered:
    st.warning("이 난이도에는 문제가 아직 없어요! 다른 난이도를 골라 보세요.")
else:
    st.write("🖱️ 위에 '새로운 문제 나와라!' 버튼을 눌러보세요!")

st.markdown("---")
st.subheader("📕 문제집 PDF 파일 내려받기")

with open(PDF_PATH, "rb") as f:
    st.download_button(
        label="📥 문제집 PDF 파일 받기",
        data=f,
        file_name="도전골든벨_어린이천문대_2025.pdf",
        mime="application/pdf"
    )

st.caption("문제집 PDF 파일을 내려받아 더 많은 문제를 볼 수 있어요!")
st.info("문제를 소리로 듣고 싶으면 '음성으로 들려줘!' 버튼을 꼭 눌러 보세요! (핸드폰, 태블릿, 컴퓨터 모두에서 잘 돼요.)")
