import streamlit as st
import pdfplumber
import random
import re

PDF_PATH = "도전골든벨_어린이천문대_2025.pdf"

# 귀엽게 스타일링
st.markdown("""
    <style>
        body { background: #ffeaff; }
        .stApp { background: #fff8fa; }
        .cute-title {
            font-size: 2.2em; font-weight: bold;
            color: #ea60b1; text-align: center;
            margin-bottom: 0.1em;
            letter-spacing: 2px;
        }
        .cute-sub {
            font-size: 1.1em; color: #666; text-align: center; margin-bottom: 1em;
        }
        .cute-card {
            background: #fff0fa;
            border-radius: 24px;
            box-shadow: 0 4px 16px #f6addf33;
            padding: 28px 18px 20px 18px;
            margin: 0.5em 0;
        }
        .cute-btn {
            background: linear-gradient(90deg,#ffc2e2 30%,#ffe478 100%);
            color: #7a4f00;
            border-radius: 18px;
            font-size: 1.18em;
            padding: 0.6em 2em;
            font-weight: bold;
            border: none;
            cursor: pointer;
            margin: 0.3em;
        }
        .cute-btn:hover { background: #fffcf2; border: 2px solid #ffc2e2; }
        .cute-radio label { font-size:1.1em; color:#d476c6; }
        .stTextInput>div>div>input {font-size: 1.2em; border-radius: 10px; border:2px solid #ff9ad2;}
        .cute-result {font-size:1.25em;}
        .cute-info {color:#ea60b1;font-size:1em;}
    </style>
""", unsafe_allow_html=True)

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
    # "또는", "or"로 분리된 정답 중 하나와 정확히 일치하면 정답!
    answer_list = [a.strip() for a in re.split(r'또는|or', answer, flags=re.IGNORECASE)]
    return user.strip() in answer_list

quiz_bank = load_quiz()
levels = ["하", "중", "상", "최상"]
level_labels = {"하":"🍭 쉬움", "중":"🧃 보통", "상":"🍰 조금 어려움", "최상":"🏆 진짜 어려움"}

st.markdown('<div class="cute-title">🍓 도전! 골든벨 퀴즈 놀이방 🍓</div>', unsafe_allow_html=True)
st.markdown('<div class="cute-sub">문제를 풀고, <b>정답을 아래 칸에 예쁘게 입력</b>해 보세요!<br>정답이 여러 개면 그 중 하나만 맞아도 OK!</div>', unsafe_allow_html=True)

# 난이도 라디오 
level = st.radio("난이도를 골라 주세요!", levels, captions=[level_labels[l] for l in levels], horizontal=True, key="level", help="내가 원하는 문제의 난이도를 골라봐요!")
filtered = [q for q in quiz_bank if q["level"] == level]

# 셔플된 문제 순서와 인덱스 관리 (중복 없이 순환)
shuffle_key = f"shuffle_order_{level}"
idx_key = f"shuffle_idx_{level}"

if shuffle_key not in st.session_state or st.session_state.get(shuffle_key) is None or len(st.session_state.get(shuffle_key, [])) != len(filtered):
    order = list(range(len(filtered)))
    random.shuffle(order)
    st.session_state[shuffle_key] = order
    st.session_state[idx_key] = 0

if "current_q" not in st.session_state:
    st.session_state.current_q = None
if "input_answer" not in st.session_state:
    st.session_state.input_answer = ""
if "result_msg" not in st.session_state:
    st.session_state.result_msg = ""

c1, c2 = st.columns([1,1])

with c1:
    if st.button("🌸 새로운 문제 나와라!", key="newq", help="셔플된 문제 중 다음 문제를 뽑아요!", use_container_width=True):
        if filtered:
            idx = st.session_state[idx_key]
            order = st.session_state[shuffle_key]
            st.session_state.current_q = filtered[order[idx]]
            st.session_state.input_answer = ""
            st.session_state.result_msg = ""
            idx += 1
            if idx >= len(filtered):
                order = list(range(len(filtered)))
                random.shuffle(order)
                idx = 0
            st.session_state[shuffle_key] = order
            st.session_state[idx_key] = idx

if st.session_state.current_q:
    st.markdown('<div class="cute-card">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:1.3em;margin-bottom:10px;"><b>🔔 문제:</b> {st.session_state.current_q["question"]}</div>', unsafe_allow_html=True)
    # 문제 읽어주는 버튼 (여성 목소리 우선)
    st.components.v1.html(f"""
        <button onclick="
            var speak = function() {{
                var voices = window.speechSynthesis.getVoices();
                var femaleVoice = voices.find(v => (v.lang === 'ko-KR') && (v.name.includes('여성') || v.name.toLowerCase().includes('female') || v.name.includes('Yuna')))
                || voices.find(v => v.lang === 'ko-KR');
                var utter = new window.SpeechSynthesisUtterance('{st.session_state.current_q["question"].replace("'", "")}');
                utter.voice = femaleVoice;
                utter.lang = 'ko-KR';
                utter.rate = 1.12;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(utter);
            }};
            if (window.speechSynthesis.getVoices().length === 0) {{
                window.speechSynthesis.onvoiceschanged = speak;
            }} else {{
                speak();
            }}
        " class="cute-btn" style="margin:10px 0 13px 0;">
            🔊 문제 읽어줘!
        </button>
    """, height=62)

    st.session_state.input_answer = st.text_input(
        "정답을 아래 칸에 써 주세요!",
        value=st.session_state.input_answer,
        key="input_box",
        placeholder="예시: 달 / moon"
    )

    if st.button("🍬 정답확인", key="check", help="정답을 맞혔는지 확인해봐요!", use_container_width=True):
        user_answer = st.session_state.input_answer.strip()
        correct_answer = st.session_state.current_q["answer"].strip()
        if user_answer == "":
            st.session_state.result_msg = f"정답을 입력해 주세요!<br><span class='cute-info'>(정답: 👉 {correct_answer})</span>"
        elif is_answer_correct(user_answer, correct_answer):
            st.session_state.result_msg = f"✅ <b>정답입니다! 정말 멋져요!</b><br><span class='cute-info'>(정답: 👉 {correct_answer})</span>"
        else:
            st.session_state.result_msg = f"❌ <b>아쉽지만 오답이에요!</b><br><span class='cute-info'>(정답: 👉 {correct_answer})</span>"

    if st.session_state.result_msg:
        if "정답입니다" in st.session_state.result_msg:
            st.markdown(f"<div class='cute-result' style='color:#27b323;background:#f0ffe7;border-radius:13px;padding:15px 10px;margin-top:10px;'>{st.session_state.result_msg}</div>", unsafe_allow_html=True)
        elif "오답" in st.session_state.result_msg:
            st.markdown(f"<div class='cute-result' style='color:#f83257;background:#fff0f2;border-radius:13px;padding:15px 10px;margin-top:10px;'>{st.session_state.result_msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='cute-result' style='color:#ea60b1;background:#fffae5;border-radius:13px;padding:15px 10px;margin-top:10px;'>{st.session_state.result_msg}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
elif not filtered:
    st.warning("이 난이도에는 문제가 아직 없어요! 다른 난이도를 골라 보세요.", icon="🦄")
else:
    st.write("👆 위에 <b>새로운 문제 나와라!</b> 버튼을 눌러보세요!", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align:center'><b>📕 문제집 PDF 파일 내려받기</b></div>", unsafe_allow_html=True)

with open(PDF_PATH, "rb") as f:
    st.download_button(
        label="🍡 문제집 PDF 파일 받기",
        data=f,
        file_name="도전골든벨_어린이천문대_2025.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.markdown("<div style='text-align:center;font-size:1em;color:#ea60b1;'>문제집 PDF 파일을 내려받아 더 많은 문제를 볼 수 있어요!</div>", unsafe_allow_html=True)
st.info("정답은 아래 칸에 써 보세요! (문제를 읽어주는 귀여운 버튼도 있어요!)")
