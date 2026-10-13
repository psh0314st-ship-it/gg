code_content = '''import streamlit as st
import json
import os
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="문학 속 인물과의 만남 | AI 문학 챗봇",
    page_icon="📚",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. Gemini API 클라이언트 설정
# -----------------------------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API 키가 설정되지 않았습니다. Streamlit Secrets 또는 환경 변수에 'GEMINI_API_KEY'를 등록해주세요.")
    st.info("로컬 테스트 시: sidebar에서 API 키를 입력할 수도 있습니다.")
    with st.sidebar:
        user_api_key = st.text_input("Gemini API Key", type="password")
        if user_api_key:
            api_key = user_api_key

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None

# -----------------------------------------------------------------------------
# 3. 작품 및 캐릭터 데이터 정의
# -----------------------------------------------------------------------------
CHARACTERS = {
    "동백꽃 - 점순이": {
        "title": "동백꽃 (김유정)",
        "name": "점순이",
        "description": "마름의 딸. 나(나작자)를 좋아하지만 표현이 서툴러 씨 씨 거리며 감자를 주기도 하고 닭싸움을 붙이기도 하는 츤데레 시골 소녀.",
        "scenes": [
            "1. 씨 씨 거리며 감자를 줄 때 (작품 초반)",
            "2. 수탉을 괴롭히고 닭싸움을 붙일 때 (작품 중반)",
            "3. 동백꽃 한창 피어난 골목에서 함께 넘어졌을 때 (작품 후반)"
        ],
        "system_instruction": """당신은 김유정의 소설 《동백꽃》에 등장하는 '점순이'입니다.
- 말투: 1930년대 강원도 시골 마름 집 딸 특유의 새침하고 직설적이며 감정 표현이 다소 서툰 츤데레 어조. ("얘!", "너 부재기(바보)냐?", "응? 내가 언제 그랬어!", "너 참 몰라서 그래?")
- 성격: 나(소작농의 아들)를 좋아하지만 겉으로는 괜히 시비를 걸고 괴롭힘. 속으로는 상대가 자기 마음을 알아주길 바람.
- 주의사항: 상대방의 입력에 대해 소설 속 상황에 몰입하여 반응하고, 대화 응답 시 반드시 아래 JSON 구조로만 답변하세요."""
    },
    "운수 좋은 날 - 김첨지": {
        "title": "운수 좋은 날 (현진건)",
        "name": "김첨지",
        "description": "일제강점기 인력거꾼. 아픈 아내를 두고 돈을 벌어야만 했던 비극적 인물. 겉으로는 거칠고 욕을 많이 하지만 속으로는 아내를 깊이 걱정함.",
        "scenes": [
            "1. 비 오는 날 아침, 아픈 아내를 뒤로하고 인력거를 끌러 나갈 때",
            "2. 선술집에서 치삼이와 술을 마시며 운수가 좋다고 자랑할 때",
            "3. 설렁탕을 사들고 집으로 돌아와 아내의 죽음을 맞이할 때"
        ],
        "system_instruction": """당신은 현진건의 소설 《운수 좋은 날》의 주인공 '김첨지'입니다.
- 말투: 1920년대 서울 하층민 인력거꾼의 거칠고 욕설이 섞인 거친 말투 ("이 오라질 년!", "이 사람아, 내가 오늘 돈을 벌었단 말이다!", "괴상하게도 오늘은 운수가 좋더니만...").
- 성격: 겉으로는 거칠게 욕을 퍼붓고 화를 내지만, 내면에는 아내에 대한 불쌍함과 가난한 현실에 대한 불안감이 가득함.
- 주의사항: 대화 응답 시 반드시 아래 JSON 구조로만 답변하세요."""
    },
    "춘향전 - 성춘향": {
        "title": "춘향전 (고전소설)",
        "name": "성춘향",
        "description": "남원 퇴기 월매의 딸. 이몽룡과의 사랑에 신의를 지키며 변학도의 수청 요구에 굴하지 않는 지조와 절개의 여인.",
        "scenes": [
            "1. 광한루에서 이몽룡을 처음 만났을 때",
            "2. 이몽룡이 한양으로 떠나며 이별을 고할 때",
            "3. 변학도의 수청을 거부하고 옥에 갇혀 있을 때"
        ],
        "system_instruction": """당신은 한국 고전소설 《춘향전》의 주인공 '성춘향'입니다.
- 말투: 단정하고 기품 있으며 유교적 덕목과 절개가 느껴지는 예스러운 어조 ("도련님", "어찌 기생의 딸이라 하여 절개를 모르겠습니까", "죽어도 변치 않으리이다").
- 성격: 신분적 한계에도 불구하고 당차고 불의에 타협하지 않으며, 이몽룡에 대한 지고지순한 사랑을 품고 있음.
- 주의사항: 대화 응답 시 반드시 아래 JSON 구조로만 답변하세요."""
    }
}

# -----------------------------------------------------------------------------
# 4. 세션 상태 초기화
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "affinity" not in st.session_state:
    st.session_state.affinity = 50
if "current_char_key" not in st.session_state:
    st.session_state.current_char_key = list(CHARACTERS.keys())[0]

# -----------------------------------------------------------------------------
# 5. 사이드바 (설정)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("📖 작품 및 캐릭터 설정")
    
    selected_char_key = st.selectbox(
        "대화할 캐릭터 선택",
        options=list(CHARACTERS.keys()),
        index=list(CHARACTERS.keys()).index(st.session_state.current_char_key)
    )
    
    # 캐릭터 변경 시 초기화
    if selected_char_key != st.session_state.current_char_key:
        st.session_state.current_char_key = selected_char_key
        st.session_state.messages = []
        st.session_state.affinity = 50
        st.rerun()

    char_info = CHARACTERS[selected_char_key]
    
    st.subheader("🎬 장면 (타임라인) 선택")
    selected_scene = st.radio("대화 시점", char_info["scenes"])
    
    is_if_mode = st.toggle("🔮 '만약에(IF)' 가상 시나리오 모드", value=False)
    if is_if_mode:
        st.info("💡 '만약에' 모드: 원작과 다른 가상의 상황을 전제로 인물과 자유롭게 대화할 수 있습니다.")
        
    st.divider()
    st.subheader("📊 인물과의 친밀도/호감도")
    st.progress(st.session_state.affinity / 100)
    st.caption(f"현재 호감도: **{st.session_state.affinity}점** / 100점")

# -----------------------------------------------------------------------------
# 6. 메인 화면 헤더
# -----------------------------------------------------------------------------
st.title(f"💬 {char_info['name']}와의 대화")
st.caption(f"**작품:** {char_info['title']} | **설정 장면:** {selected_scene}")
st.write(f"> {char_info['description']}")

# 대화 기록 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "details" in msg:
            details = msg["details"]
            with st.expander("🔍 인물의 내면 & 원작 정보 보기"):
                st.write(f"**💡 속마음:** {details.get('inner_thought', 'N/A')}")
                st.write(f"**📜 관련 원작 구절:** {details.get('quote', 'N/A')}")
                if details.get("question_to_user"):
                    st.info(f"❓ **{char_info['name']}의 질문:** {details['question_to_user']}")

# -----------------------------------------------------------------------------
# 7. AI 대화 처리 함수
# -----------------------------------------------------------------------------
def get_character_response(user_input):
    prompt_context = f"""
[현재 소설 및 캐릭터]: {char_info['title']} - {char_info['name']}
[선택한 장면/시점]: {selected_scene}
[만약에(IF) 모드 여부]: {'활성화됨' if is_if_mode else '비활성화(원작 충실)'}
[현재 호감도]: {st.session_state.affinity}/100

[사용자 입력]: {user_input}

위 사용자 입력에 반응하여 {char_info['name']}의 정체성과 말투를 완벽히 유지하며 대답하세요.
반드시 아래 JSON 형식으로만 결과를 출력해야 합니다. 다른 텍스트는 포함하지 마세요.

{{
  "reply": "인물의 대화 답변 (말투와 어조를 완벽히 유지)",
  "inner_thought": "인물이 겉으로 한 말 뒤에 숨겨진 실제 속마음이나 심리",
  "quote": "이 대화 상황과 관련된 원작 소설 속 실제 구절이나 관련 문장",
  "affinity_change": 숫자 (사용자의 말에 따라 호감도 변화량: -10 ~ +10 사이 정수),
  "question_to_user": "대화 후 인물이 사용자에게 던지는 반문이나 역질문 (optional)"
}}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_context,
            config=types.GenerateContentConfig(
                system_instruction=char_info["system_instruction"],
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        st.error(f"대화 응답 생성 중 오류가 발생했습니다: {e}")
        return None

# -----------------------------------------------------------------------------
# 8. 사용자 입력 처리
# -----------------------------------------------------------------------------
if user_prompt := st.chat_input(f"{char_info['name']}에게 말해보세요..."):
    if not client:
        st.error("API 키가 설정되지 않아 대화를 진행할 수 없습니다.")
        st.stop()
        
    # 사용자 메시지 저장 및 표시
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner(f"{char_info['name']}(이)가 생각 중입니다..."):
            ai_data = get_character_response(user_prompt)
            
            if ai_data:
                reply = ai_data.get("reply", "...")
                st.write(reply)
                
                # 호감도 업데이트
                aff_change = ai_data.get("affinity_change", 0)
                st.session_state.affinity = max(0, min(100, st.session_state.affinity + aff_change))
                
                # 상세 정보 표시
                with st.expander("🔍 인물의 내면 & 원작 정보 보기"):
                    st.write(f"**💡 속마음:** {ai_data.get('inner_thought', '')}")
                    st.write(f"**📜 관련 원작 구절:** {ai_data.get('quote', '')}")
                    if ai_data.get("question_to_user"):
                        st.info(f"❓ **{char_info['name']}의 질문:** {ai_data['question_to_user']}")
                
                # 메세지 저장
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply,
                    "details": ai_data
                })

# -----------------------------------------------------------------------------
# 9. 대화록 / 인터뷰 보고서 다운로드 기능
# -----------------------------------------------------------------------------
if st.session_state.messages:
