import streamlit as st
import pdfplumber
import random
import re

PDF_PATH = "도전골든벨_어린이천문대_2025.pdf"

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
            text += page.extract_text() + "\n"

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

st.title("🌟 도전! 골든벨 랜덤 퀴즈 (자동 음성 출력)")
st.write("난이도를 고르고 [질문 랜덤 출제] 버튼을 누르면, 화면에 문제도 보이고 소리도 자동으로 나와요!")

level = st.radio("난이도를 골라보세요!", levels, horizontal=True)
filtered = [q for q in quiz_bank if q["level"] == level]

if "current_q" not in st.session_state:
    st.session_state.current_q = None
    st.session_state.show_a = False

col1, col2 = st.columns(2)

with col1:
    if st.button("🎲 질문 랜덤 출제"):
        st.session_state.current_q = random.choice(filtered) if filtered else None
        st.session_state.show_a = False

with col2:
    if st.button("정답 보기"):
        st.session_state.show_a = True

if st.session_state.current_q:
    st.info("Q. " + st.session_state.current_q["question"])
    # 문제 나올 때마다 자동으로 음성 재생 (브라우저 TTS)
    st.components.v1.html(f"""
        <script>
            var utter = new window.SpeechSynthesisUtterance("{st.session_state.current_q["question"].replace('"','').replace("'",'')}");
            utter.lang = "ko-KR";
            utter.rate = 1.0;  // 읽는 속도 (1.0이 기본)
            window.speechSynthesis.cancel(); // 이전 읽기 멈춤
            window.speechSynthesis.speak(utter);
        </script>
    """, height=0)

    if st.session_state.show_a:
        st.success("A. " + st.session_state.current_q["answer"])
elif not filtered:
    st.warning("선택한 난이도의 문제가 아직 없어요!")
else:
    st.write("⬅️ [질문 랜덤 출제] 버튼을 눌러주세요!")

st.caption("문제는 화면에 뜨고, 동시에 자동으로 소리도 나와요!")
