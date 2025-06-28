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

def is_answer_correct(user, answer):
    # "또는"이나 "or"로 분리된 정답 리스트 중 하나와 정확히 일치할 때만 정답!
    answer_list = [a.strip() for a in re.split(r'또는|or', answer, flags=re.IGNORECASE)]
    return user.strip() in answer_list

quiz_bank = load_quiz()
levels = ["하", "중", "상", "최상"]

st.title("🎉 도전! 골든벨 퀴즈 놀이방")
st.write("문제를 보고 정답을 직접 쓰거나, 마이크로 말해서 입력할 수 있어요! (정답에 '또는', 'or'이 있으면 그 중 하나만 맞춰도 정답!)")

st.markdown("#### 난이도를 골라 주세요!")
level = st.radio("", levels, horizontal=True, captions=["쉬움", "보통", "조금 어려움", "진짜 어려움"])
filtered = [q for q in quiz_bank if q["level"] == level]

# 세션 상태
if "current_q" not in st.session_state:
    st.session_state.current_q = None
if "input_answer" not in st.session_state:
    st.session_state.input_answer = ""
if "result_msg" not in st.session_state:
    st.session_state.result_msg = ""

col1, col2 = st.columns(2)

with col1:
    if st.button("🧩 새로운 문제 나와라!"):
        st.session_state.current_q = random.choice(filtered) if filtered else None
        st.session_state.input_answer = ""
        st.session_state.result_msg = ""

if st.session_state.current_q:
    st.info("🔔 문제: " + st.session_state.current_q["question"])

    # 마이크 버튼만 단독 표시
    st.markdown("""
    <div style="display:flex;gap:12px;align-items:center;">
      <button id="voice_btn" style="font-size:22px;padding:7px 18px;border-radius:50%;background:#ffd700;border:none;cursor:pointer;" title="마이크로 말하기">🎤 정답 말하기</button>
    </div>
    <script>
    let recognizing = false;
    let recognition;
    document.getElementById('voice_btn').onclick = function() {
        if (!('webkitSpeechRecognition' in window)) {
            alert('이 브라우저는 음성 인식을 지원하지 않아요!');
            return;
        }
        if (!recognition) {
            recognition = new webkitSpeechRecognition();
            recognition.lang = 'ko-KR';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
            recognition.onresult = function(event) {
                var speechResult = event.results[0][0].transcript;
                // Streamlit의 실제 입력창에 강제로 입력
                const input = window.parent.document.querySelector('input[data-testid="stTextInput"]');
                if(input) {
                    input.value = speechResult;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
            };
            recognition.onerror = function(event) {
                alert('음성 인식 오류가 발생했어요: ' + event.error);
            };
            recognition.onend = function() {
                recognizing = false;
            };
        }
        if (!recognizing) {
            recognition.start();
            recognizing = true;
        } else {
            recognition.stop();
            recognizing = false;
        }
    };
    </script>
    """, unsafe_allow_html=True)

    # 정답 입력창
    st.session_state.input_answer = st.text_input(
        "정답을 여기에 써 주세요! (위 마이크 버튼을 누르고 말하면 여기에 자동 입력돼요)",
        value=st.session_state.input_answer,
        key="input_box"
    )

    # 정답확인
    if st.button("정답확인"):
        user_answer = st.session_state.input_answer.strip()
        correct_answer = st.session_state.current_q["answer"].strip()
        if user_answer == "":
            st.session_state.result_msg = f"정답을 입력해 주세요! (정답: 👉 {correct_answer})"
        elif is_answer_correct(user_answer, correct_answer):
            st.session_state.result_msg = f"✅ 정답입니다! 정말 멋져요!\n\n(정답: 👉 {correct_answer})"
        else:
            st.session_state.result_msg = f"❌ 오답이에요! 다시 도전해 보세요.\n\n(정답: 👉 {correct_answer})"

    # 결과 메시지(텍스트로 안내)
    if st.session_state.result_msg:
        if "정답입니다" in st.session_state.result_msg:
            st.success(st.session_state.result_msg)
        elif "오답" in st.session_state.result_msg:
            st.error(st.session_state.result_msg)
        else:
            st.info(st.session_state.result_msg)
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
st.info("정답은 아래 칸에 직접 쓰거나, 🎤 마이크 버튼을 누르고 말해도 입력돼요! (크롬, 삼성인터넷 등 최신 브라우저 권장)")
