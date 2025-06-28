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

st.title("🎉 도전! 골든벨 퀴즈 놀이방")
st.write("문제를 보고, 내가 생각한 정답을 써 보거나, 그냥 바로 정답확인 버튼을 눌러도 정답이 나와요! 궁금한 문제나 결과는 소리로도 들을 수 있어요.")

st.markdown("#### 난이도를 골라 주세요!")
level = st.radio("", levels, horizontal=True, captions=["쉬움", "보통", "조금 어려움", "진짜 어려움"])

filtered = [q for q in quiz_bank if q["level"] == level]

if "current_q" not in st.session_state:
    st.session_state.current_q = None
    st.session_state.input_answer = ""
    st.session_state.result_msg = ""
    st.session_state.result_msg_tts = ""

col1, col2 = st.columns(2)

with col1:
    if st.button("🧩 새로운 문제 나와라!"):
        st.session_state.current_q = random.choice(filtered) if filtered else None
        st.session_state.input_answer = ""
        st.session_state.result_msg = ""
        st.session_state.result_msg_tts = ""

# 문제, 정답 입력, 정답확인, 음성출력 버튼
if st.session_state.current_q:
    st.info("🔔 문제: " + st.session_state.current_q["question"])

    # "음성으로 들려줘!" 버튼
    st.components.v1.html(f"""
        <button onclick="
            var speak = function() {{
                var voices = window.speechSynthesis.getVoices();
                var utter = new window.SpeechSynthesisUtterance('{st.session_state.current_q["question"].replace("'", "")}');
                var cuteVoice = voices.find(v => v.name.includes('Yuna')) 
                    || voices.find(v => v.lang=='ko-KR' && v.name.includes('여성'))
                    || voices.find(v => v.lang=='ko-KR');
                if(cuteVoice) utter.voice = cuteVoice;
                utter.lang = 'ko-KR';
                utter.rate = 1.15;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(utter);
            }};
            if (window.speechSynthesis.getVoices().length === 0) {{
                window.speechSynthesis.onvoiceschanged = speak;
            }} else {{
                speak();
            }}
        " style="font-size:18px;padding:8px 20px;border-radius:12px;background:#ffd700;border:none;cursor:pointer;margin-bottom:8px;">
            🔊 음성으로 들려줘!
        </button>
    """, height=70)

    # 정답 입력칸
    st.session_state.input_answer = st.text_input(
        "내가 생각한 정답을 여기에 써 보세요! (안 써도 돼요)",
        value=st.session_state.input_answer,
        key="input_box"
    )

    # 정답 확인 버튼
    if st.button("정답확인"):
        user_answer = st.session_state.input_answer.strip()
        correct_answer = st.session_state.current_q["answer"].strip()
        if user_answer == "":
            # 입력을 안 했으면 바로 정답만 보여주기!
            st.session_state.result_msg = f"정답은 👉 {correct_answer} 입니다!"
            st.session_state.result_msg_tts = f"정답은 {correct_answer} 입니다!"
        elif user_answer == correct_answer:
            st.session_state.result_msg = "🎉 정답이에요! 정말 멋져요!"
            st.session_state.result_msg_tts = "정답이에요! 정말 멋져요!"
        else:
            st.session_state.result_msg = f"🙅 아쉽지만 오답이에요!\n\n정답은 👉 {correct_answer} 입니다."
            st.session_state.result_msg_tts = f"아쉽지만 오답이에요. 정답은 {correct_answer} 입니다."

    # 결과 메시지 출력 및 음성 재생
    if st.session_state.result_msg:
        if "정답이에요" in st.session_state.result_msg:
            st.success(st.session_state.result_msg)
        elif "오답" in st.session_state.result_msg:
            st.error(st.session_state.result_msg)
        else:
            st.info(st.session_state.result_msg)

        # 정답 결과를 음성으로 출력 (자동)
        st.components.v1.html(f"""
            <script>
                var speak = function() {{
                    var voices = window.speechSynthesis.getVoices();
                    var utter = new window.SpeechSynthesisUtterance('{st.session_state.result_msg_tts}');
                    var cuteVoice = voices.find(v => v.name.includes('Yuna')) 
                        || voices.find(v => v.lang=='ko-KR' && v.name.includes('여성'))
                        || voices.find(v => v.lang=='ko-KR');
                    if(cuteVoice) utter.voice = cuteVoice;
                    utter.lang = 'ko-KR';
                    utter.rate = 1.15;
                    window.speechSynthesis.cancel();
                    window.speechSynthesis.speak(utter);
                }};
                if (window.speechSynthesis.getVoices().length === 0) {{
                    window.speechSynthesis.onvoiceschanged = speak;
                }} else {{
                    speak();
                }}
            </script>
        """, height=0)
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
st.info("문제나 정답 결과를 소리로 듣고 싶으면 '음성으로 들려줘!' 버튼이나 정답확인 버튼을 눌러보세요!")
