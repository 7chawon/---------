import streamlit as st
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import base64
import random
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# AI 이미지 생성 결과 모달
@st.dialog("AI로 이미지 생성", width="large")
def ai_image_result_dialog():
    st.markdown("""
    <div style="background: #2a2a2a; padding: 15px; border-radius: 8px; margin-bottom: 20px;
         display: flex; justify-content: space-between; align-items: center;">
        <p style="color: #ccc; font-size: 14px; margin: 0;">+ 버튼을 누르시면 라벨 이미지에 추가됩니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 재생성 버튼
    col_spacer, col_regen = st.columns([4, 1])
    with col_regen:
        if st.button("재생성", type="primary", use_container_width=True):
            st.session_state.ai_generated_images = None
            st.session_state.ai_generating = True
            st.rerun()
    
    # 이미지 생성 중이거나 이미지가 없으면 생성
    if st.session_state.get('ai_generating', False) or not st.session_state.get('ai_generated_images'):
        # 로딩 애니메이션 CSS
        st.markdown("""
        <style>
        @keyframes dotPulse {
            0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
            40% { opacity: 1; transform: scale(1.2); }
        }
        .loading-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            margin: 0 4px;
            background: #888;
            border-radius: 50%;
            animation: dotPulse 1.4s infinite ease-in-out;
        }
        .loading-dot:nth-child(1) { animation-delay: 0s; }
        .loading-dot:nth-child(2) { animation-delay: 0.2s; }
        .loading-dot:nth-child(3) { animation-delay: 0.4s; }
        </style>
        """, unsafe_allow_html=True)
        
        # 로딩 중 표시 (1개 - 컴팩트한 세로 비율)
        st.markdown(f"""
        <div style="width: 200px; height: 350px; margin: 0 auto; background: #1a1a1a; border-radius: 8px;
             border: 1px solid #333; display: flex; align-items: center; justify-content: center;">
            <div>
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # API 호출해서 이미지 생성
        with st.spinner("🎨 AI가 이미지를 생성 중입니다..."):
            try:
                # AI 선택 항목들 가져오기
                selections = st.session_state.get('ai_selections', {})
                user_prompt = st.session_state.form_data.get('ai_prompt', '')
                art_style = st.session_state.form_data.get('art_style', '단색 배경')
                reference_style = st.session_state.get('reference_style_desc', '')
                
                # 선택 항목들을 구체적인 프롬프트로 변환
                subject = selections.get('subject', '')
                subject_type = selections.get('animal_type', '') or selections.get('object_type', '') or selections.get('plant_type', '')
                gender = selections.get('gender', '')
                pose = selections.get('pose', '')
                weather = selections.get('weather', '')
                time_of_day = selections.get('time', '')
                bg_elements = selections.get('bg_elements', [])
                mood = selections.get('mood', '')
                amount = selections.get('amount', '')
                
                # 주제별 상세 프롬프트 구성
                subject_prompt = ""
                if subject == "동물":
                    animal = subject_type if subject_type else "고양이"
                    gender_desc = f"{gender} " if gender and gender != "성별 무관" else ""
                    pose_desc = f"{pose} " if pose else "정면을 바라보는 "
                    subject_prompt = f"A beautiful {gender_desc}{animal}, {pose_desc}pose, highly detailed fur texture, expressive eyes, photorealistic animal portrait"
                elif subject == "사람":
                    gender_desc = "남성" if gender == "남자" else "여성" if gender == "여자" else "사람"
                    age = selections.get('age', '20대')
                    pose_desc = pose if pose else "우아한 포즈"
                    subject_prompt = f"A beautiful {age} {gender_desc}, {pose_desc}, elegant portrait, expressive face, high fashion photography style"
                elif subject == "식물":
                    plant = subject_type if subject_type else "꽃"
                    amount_desc = amount if amount else "적당한 양의"
                    subject_prompt = f"Beautiful {plant}, {amount_desc}, botanical illustration, delicate petals, vibrant colors, detailed texture"
                elif subject == "사물":
                    obj = subject_type if subject_type else "보석"
                    subject_prompt = f"Elegant {obj}, luxury product photography style, dramatic lighting, high-end aesthetic, detailed craftsmanship"
                else:
                    subject_prompt = user_prompt if user_prompt else "우아한 추상적 예술 작품"
                
                # 배경 및 분위기 프롬프트
                weather_prompt = ""
                if weather:
                    weather_map = {
                        "흐린 날씨": "overcast sky, soft diffused lighting, moody atmosphere",
                        "맑은 날씨": "clear blue sky, bright sunlight, vibrant atmosphere"
                    }
                    weather_prompt = weather_map.get(weather, "")
                
                time_prompt = ""
                if time_of_day:
                    time_map = {
                        "낮": "daylight, warm golden hour lighting, sun-drenched",
                        "밤": "nighttime, moonlight, starry sky, mysterious atmosphere"
                    }
                    time_prompt = time_map.get(time_of_day, "")
                
                bg_prompt = ""
                if bg_elements:
                    element_map = {
                        "구름": "fluffy clouds",
                        "해": "bright sun",
                        "달": "glowing moon",
                        "별": "twinkling stars",
                        "비": "rain drops, wet atmosphere"
                    }
                    bg_items = [element_map.get(e, e) for e in bg_elements]
                    bg_prompt = f"Background elements: {', '.join(bg_items)}"
                
                mood_prompt = ""
                if mood:
                    mood_map = {
                        "우아한": "elegant, sophisticated, refined",
                        "신비로운": "mystical, ethereal, magical",
                        "청량한": "fresh, cool, crisp",
                        "따뜻한": "warm, cozy, inviting",
                        "고급스러운": "luxurious, premium, opulent",
                        "빈티지한": "vintage, nostalgic, classic"
                    }
                    mood_prompt = mood_map.get(mood, mood)
                
                # 아트 스타일 영문 변환
                style_map = {
                    "단색 배경": "clean solid color background, minimalist luxury, studio lighting",
                    "Oil Painting (유화)": "masterful oil painting style, visible thick brushstrokes, rich impasto textures, classical European master painting quality, canvas texture",
                    "Watercolor (수채화)": "delicate hand-painted watercolor, soft ethereal washes, subtle color bleeding, wet-on-wet technique, traditional watercolor paper texture",
                    "Abstract (추상화)": "neo-expressionist art, bold expressive brushstrokes, contemporary fine art, gallery-worthy",
                    "Minimal Gradient (그라데이션)": "sophisticated smooth gradient, luxurious color transitions, minimalist design",
                    "Photography (포토그래피)": "ultra-realistic photography, professional DSLR camera quality, sharp focus, natural lighting, photorealistic, 8K resolution, detailed texture, lifelike appearance"
                }
                style_desc = style_map.get(art_style, "minimalist, elegant, hand-crafted quality")
                
                # 레퍼런스 이미지 스타일 추가
                reference_part = ""
                if reference_style:
                    reference_part = f"\n                Reference Style Guide: {reference_style}"
                
                # 최종 프롬프트 구성 - "artwork", "painting", "canvas" 단어 완전 제거
                full_prompt = f"""
                Generate a beautiful vertical image.
                
                === WHAT TO CREATE (PRIORITY) ===
                {user_prompt}
                {subject_prompt}
                
                === VISUAL STYLE ===
                {style_desc}
                
                === MOOD & ENVIRONMENT ===
                {mood_prompt if mood_prompt else 'Elegant and sophisticated'}
                {weather_prompt}
                {time_prompt}
                {bg_prompt}
                {reference_part}
                
                === MANDATORY RULES ===
                - Generate a DIRECT VIEW of the scene - as if taking a photo
                - The subject and background must fill the ENTIRE image edge-to-edge
                - NO empty space, NO margins, NO borders around the image
                - DO NOT create a picture of a picture
                - DO NOT show any frames, walls, or room settings
                - DO NOT include any picture frames (gold, wood, black, or any kind)
                - DO NOT show this as something hanging on a wall
                - DO NOT add any text, letters, signatures, or watermarks
                - DO NOT add objects that weren't requested
                - The generated image IS the scene itself, not a depiction of it
                
                Think of this as taking a photograph directly of the subject, not photographing a framed picture.
                """
                
                # DALL-E API 호출 (1개 이미지) - 세로 직사각형 필수
                generated_images = []
                for i in range(1):  # 1개만 생성하여 속도 향상
                    try:
                        response = client.images.generate(
                            model="dall-e-3",
                            prompt=full_prompt,
                            size="1024x1792",  # 세로로 긴 비율 필수
                            quality="standard",
                            n=1,
                        )
                        img_url = response.data[0].url
                        res = requests.get(img_url)
                        img = Image.open(BytesIO(res.content))
                        generated_images.append(img)
                    except Exception as e:
                        # API 실패 시 테스트용 이미지 생성 (세로 비율)
                        test_img = Image.new('RGBA', (512, 896), color='#3d5afe')
                        generated_images.append(test_img)
                
                st.session_state.ai_generated_images = generated_images
                st.session_state.ai_generating = False
                st.rerun()
                
            except Exception as e:
                st.error(f"이미지 생성 중 오류: {e}")
                st.session_state.ai_generating = False
    else:
        # 생성된 이미지 표시 (1개)
        for i, img in enumerate(st.session_state.ai_generated_images):
            st.image(img, use_container_width=True)
            if st.button("➕ 이 이미지 사용하기", key=f"select_ai_img_{i}", use_container_width=True):
                # 이미지를 label_images 리스트에 추가
                if 'label_images' not in st.session_state.form_data:
                    st.session_state.form_data['label_images'] = []
                
                # 최대 2개까지만 추가 가능
                if len(st.session_state.form_data['label_images']) < 2:
                    st.session_state.form_data['label_images'].append(img)
                    # 첫 이미지면 자동 선택
                    if st.session_state.form_data.get('selected_image_idx') is None:
                        st.session_state.form_data['selected_image_idx'] = len(st.session_state.form_data['label_images']) - 1
                    st.success("이미지가 추가되었습니다!")
                else:
                    st.warning("최대 2개까지만 추가할 수 있습니다.")
                
                st.session_state.ai_generated_images = None
                st.rerun()

# AI 이미지 생성 모달 - 채팅 인터페이스
@st.dialog("AI로 이미지 생성", width="large")
def ai_image_dialog():
    # 2단계 미선택 항목 체크 및 안내 메시지 생성
    form_data = st.session_state.form_data
    missing_items = []
    
    selected_vibes = form_data.get('selected_vibes', [])
    if not selected_vibes:
        missing_items.append("향의 분위기")
    
    memory = form_data.get('memory', '').strip()
    if not memory:
        missing_items.append("담고 싶은 분위기/기억")
    
    art_style = form_data.get('art_style', None)
    if not art_style:
        missing_items.append("아트 스타일")
    
    # 초기 안내 메시지 구성
    initial_message = "안녕하세요! 라벨에 어떤 주제를 담고 싶으신가요? 🎨\n\n"
    
    if missing_items:
        initial_message += f"⚠️ **아직 선택하지 않은 항목이 있어요:**\n"
        for item in missing_items:
            initial_message += f"  • {item}\n"
        initial_message += "\n이 항목들은 대화를 통해 정할 수 있어요!\n\n"
    
    if selected_vibes:
        initial_message += f"✅ **선택된 분위기:** {', '.join(selected_vibes)}\n"
    if memory:
        initial_message += f"✅ **담고 싶은 기억:** {memory[:50]}{'...' if len(memory) > 50 else ''}\n"
    if art_style:
        initial_message += f"✅ **아트 스타일:** {art_style}\n"
    
    initial_message += "\n아래에서 선택하거나 직접 입력해주세요!"
    
    # 채팅 히스토리 초기화
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": initial_message}
        ]
    if 'chat_step' not in st.session_state:
        st.session_state.chat_step = 1  # 1: 주제, 2: 세부사항, 3: 분위기, 4: 확인
    
    # 채팅 영역 스타일 + 자동 스크롤
    st.markdown("""
    <style>
    .chat-container {
        max-height: 350px;
        overflow-y: auto;
        padding: 10px;
        background: #1a1a1a;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .user-msg {
        background: #3d5afe;
        color: white;
        padding: 10px 15px;
        border-radius: 18px 18px 5px 18px;
        margin: 8px 0;
        margin-left: 20%;
        text-align: right;
    }
    .assistant-msg {
        background: #333;
        color: #eee;
        padding: 10px 15px;
        border-radius: 18px 18px 18px 5px;
        margin: 8px 0;
        margin-right: 20%;
    }
    </style>
    <script>
    // 자동 스크롤 함수
    function scrollToBottom() {
        const containers = document.querySelectorAll('[data-testid="stVerticalBlock"]');
        containers.forEach(container => {
            if (container.style.height === '300px' || container.style.maxHeight === '300px') {
                container.scrollTop = container.scrollHeight;
            }
        });
        // iframe 내부의 스크롤 가능한 컨테이너도 확인
        const scrollContainers = document.querySelectorAll('[style*="overflow"]');
        scrollContainers.forEach(el => {
            if (el.scrollHeight > el.clientHeight) {
                el.scrollTop = el.scrollHeight;
            }
        });
    }
    // 페이지 로드 후 실행
    setTimeout(scrollToBottom, 100);
    setTimeout(scrollToBottom, 500);
    </script>
    """, unsafe_allow_html=True)
    
    # 채팅 메시지 표시
    chat_container = st.container(height=300)
    with chat_container:
        for msg in st.session_state.chat_messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        
        # 자동 스크롤을 위한 앵커
        st.markdown('<div id="chat-bottom"></div>', unsafe_allow_html=True)
    
    # 자동 스크롤 JavaScript (st.components 사용)
    import streamlit.components.v1 as components
    components.html("""
    <script>
        const chatContainers = window.parent.document.querySelectorAll('[data-testid="stVerticalBlockBorderWrapper"]');
        chatContainers.forEach(container => {
            const inner = container.querySelector('[data-testid="stVerticalBlock"]');
            if (inner && inner.parentElement.style.height) {
                inner.scrollTop = inner.scrollHeight;
            }
        });
        
        // 추가로 모든 스크롤 가능한 요소 확인
        const allScrollable = window.parent.document.querySelectorAll('*');
        allScrollable.forEach(el => {
            const style = window.getComputedStyle(el);
            if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight) {
                if (el.scrollHeight < 500) {  // 채팅 컨테이너 크기 정도
                    el.scrollTop = el.scrollHeight;
                }
            }
        });
    </script>
    """, height=0)
    
    st.write("")
    
    # 아트 스타일에 따른 기본 레퍼런스 이미지 매핑
    art_style_images = {
        "Oil Painting (유화)": "style_oil.png",
        "Watercolor (수채화)": "style_watercolor.png",
        "Abstract (추상화)": "style_abstract.png",
        "Photography (포토그래피)": "style_photo.png"
    }
    
    # 현재 선택된 아트 스타일
    current_art_style = st.session_state.form_data.get('art_style', None)
    
    # 참고사진 첨부 (간소화)
    st.markdown("---")
    st.markdown("**📎 참고사진** *(선택사항)*")
    col_upload, _ = st.columns([1, 2])
    with col_upload:
        ref_image = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="ref_image_upload", label_visibility="collapsed")
    
    if ref_image:
        st.session_state.user_uploaded_ref = True
        ref_img = Image.open(ref_image)
        col_img, col_btn = st.columns([1, 2])
        with col_img:
            st.image(ref_img, width=80)
        with col_btn:
            if st.button("🔍 분석", use_container_width=True):
                with st.spinner("분석 중..."):
                    try:
                        import base64
                        buffered = BytesIO()
                        ref_img.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()
                        
                        analysis_response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Analyze this image and describe its artistic style, color palette, mood, and visual characteristics in detail. Focus on: 1) Art style (painting technique, brushwork), 2) Color palette and tones, 3) Mood and atmosphere, 4) Composition style. Respond in English, concise but detailed (3-4 sentences)."
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/png;base64,{img_base64}"
                                            }
                                        }
                                    ]
                                }
                            ],
                            max_tokens=300
                        )
                        
                        style_desc = analysis_response.choices[0].message.content
                        st.session_state.reference_style_desc = style_desc
                        st.session_state.chat_messages.append({"role": "assistant", "content": f"🎨 참고사진 분석 완료! 이 스타일을 반영할게요."})
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"분석 실패: {e}")
    
    if st.session_state.get('reference_style_desc'):
        st.caption("✅ 참고 스타일 적용됨")
    
    st.write("")
    
    # 채팅 입력창 (form으로 감싸서 엔터로 전송 가능하게)
    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_send = st.columns([5, 1])
        with col_input:
            user_input = st.text_input(
                "메시지 입력",
                placeholder="원하는 라벨 느낌을 자유롭게 설명해주세요...",
                label_visibility="collapsed"
            )
        with col_send:
            send_clicked = st.form_submit_button("전송", type="primary", use_container_width=True)
    
    if send_clicked and user_input:
        # 사용자 메시지 추가
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        
        # 긍정 답변 또는 생성 요청 감지
        positive_keywords = ["네", "응", "좋아", "그래", "만들어", "생성해", "부탁해", "ㅇㅇ", "ㅇㅋ", "ok", "yes", "예"]
        user_lower = user_input.lower().strip()
        
        # 마지막 AI 메시지가 "생성할까요?" 류인지 확인
        last_ai_msg = ""
        for msg in reversed(st.session_state.chat_messages[:-1]):
            if msg["role"] == "assistant":
                last_ai_msg = msg["content"]
                break
        
        is_asking_generate = "생성할까요" in last_ai_msg or "만들어볼까요" in last_ai_msg
        is_final_confirm = "최종 확인" in last_ai_msg or "정말 생성" in last_ai_msg
        is_positive_response = any(kw in user_lower for kw in positive_keywords)
        is_direct_request = any(kw in user_lower for kw in ["생성해", "만들어", "생성 해", "만들어 줘"])
        
        # 최종 확인 후 긍정 답변인 경우에만 이미지 생성
        if is_final_confirm and is_positive_response:
            # 이전 대화에서 프롬프트 추출 (생성 요청 제외)
            user_messages = [m["content"] for m in st.session_state.chat_messages if m["role"] == "user"]
            # 긍정 답변 제외하고 실제 요청 내용만
            prompt_messages = [m for m in user_messages[:-1] if not any(kw in m.lower() for kw in positive_keywords)]
            if prompt_messages:
                final_prompt = " ".join(prompt_messages[-3:])
            else:
                final_prompt = " ".join(user_messages[-3:])
            
            st.session_state.form_data['ai_prompt'] = final_prompt
            st.session_state.ai_generating = True
            st.session_state.show_ai_dialog = False
            st.session_state.show_ai_result = True
            st.rerun()
        # 첫 번째 긍정 답변 또는 직접 생성 요청 - 한 번 더 확인
        elif (is_asking_generate and is_positive_response) or is_direct_request:
            st.session_state.chat_messages.append({"role": "assistant", "content": "🎨 **최종 확인**\n\n지금까지 선택하신 내용으로 AI 이미지를 생성합니다.\n정말 생성할까요? (네/아니오)"})
            st.rerun()
        else:
            # 단계별 질문 진행
            current_step = st.session_state.chat_step
            
            try:
                system_prompt = """당신은 향수 라벨 디자인 전문가입니다. 사용자의 답변에 맞게 다음 질문을 하세요.
현재 대화 단계에 따라 순서대로 질문하세요:

단계 1 (주제 선택 후): 세부 사항을 물어보세요.
- 사람이면: "멋져요! 👤 남성인가요, 여성인가요? 그리고 대략적인 나이대가 어떻게 될까요?"
- 동물이면: "귀여워요! 🐾 어떤 동물인가요? 그리고 암컷/수컷 중 어떤 느낌을 원하시나요?"
- 식물/자연이면: "자연스럽네요! 🌿 어떤 식물이나 자연 요소를 원하시나요?"
- 사물/추상이면: "흥미로워요! ✨ 어떤 사물이나 추상적 개념인가요?"

단계 2 (세부 사항 후): 날씨/시간대를 물어보세요.
"좋아요! 🌤️ 배경이 되는 날씨나 시간대는 어떤 느낌이면 좋을까요?\n예: 맑은 날, 흐린 날, 비오는 날, 눈오는 날, 낮, 밤, 새벽, 황혼 등"

단계 3 (날씨 후): 색감을 물어보세요.
"멋져요! 🎨 전체적인 색감은 어떤 톤이 좋을까요?\n예: 따뜻한 톤, 차가운 톤, 파스텔, 비비드, 모노톤, 골드/로즈골드 등"

단계 4 (색감 후): 자연 요소 추가 여부를 물어보세요.
"거의 다 왔어요! 🌿 배경에 풀, 나무, 꽃 같은 자연 요소를 추가할까요?\n예: 없음, 약간의 풀잎, 꽃잎, 나뭇잎, 숲 배경 등"

단계 5 (자연요소 후): 분위기를 물어보세요.
"마지막이에요! ✨ 전체적인 분위기는 어떻게 할까요?\n예: 우아한, 신비로운, 청량한, 따뜻한, 고급스러운, 빈티지한, 모던한"

단계 6 (분위기 후): 최종 확인하세요.
지금까지 선택한 내용을 요약하고 "이 느낌으로 이미지를 생성할까요?"라고 물어보세요.

항상 짧고 친근하게 답변하세요 (2-3문장)."""
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *st.session_state.chat_messages[-6:]
                    ],
                    max_tokens=250
                )
                ai_response = response.choices[0].message.content
                
                # 단계 업데이트
                if current_step < 7:
                    st.session_state.chat_step = current_step + 1
                    
            except:
                ai_response = "좋은 선택이에요! ✨ 이 느낌으로 이미지를 생성할까요?"
            
            st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
            st.rerun()
    
    st.write("")
    
    # 선택 상태 저장
    if 'ai_selections' not in st.session_state:
        st.session_state.ai_selections = {}
    
    # 추천 선택지 (단계별로 다르게 표시)
    current_step = st.session_state.get('chat_step', 1)
    selections = st.session_state.ai_selections
    
    # 1단계: 주제 선택 (사람, 동물, 사물, 식물)
    if current_step == 1:
        st.markdown("**🎯 주제 선택** (클릭하면 자동 입력)")
        subject_options = [
            ("👤 사람", "사람"),
            ("🐾 동물", "동물"),
            ("💎 사물", "사물"),
            ("🌸 식물", "식물")
        ]
        kw_cols = st.columns(4)
        for i, (label, value) in enumerate(subject_options):
            with kw_cols[i]:
                if st.button(label, key=f"subject_{i}", use_container_width=True):
                    st.session_state.ai_selections['subject'] = value
                    st.session_state.chat_messages.append({"role": "user", "content": f"{value}을 주제로 하고 싶어요"})
                    
                    # 주제별 첫 질문
                    if value == "사물":
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 💎 어떤 종류의 사물인가요?\n\n예: 보석, 향수병, 악기, 자동차, 시계, 가구 등"})
                        st.session_state.chat_step = 2  # 사물 종류 선택
                    elif value == "동물":
                        st.session_state.chat_messages.append({"role": "assistant", "content": "귀여워요! 🐾 어떤 동물인가요?\n\n예: 고양이, 강아지, 사자, 호랑이, 토끼, 새, 나비 등"})
                        st.session_state.chat_step = 2  # 동물 종류 선택
                    elif value == "사람":
                        st.session_state.chat_messages.append({"role": "assistant", "content": "멋져요! 👤 성별을 선택해주세요."})
                        st.session_state.chat_step = 2
                    else:  # 식물
                        st.session_state.chat_messages.append({"role": "assistant", "content": "자연스럽네요! 🌸 어떤 종류의 식물인가요?"})
                        st.session_state.chat_step = 2
                    st.rerun()
    
    # 2단계: 주제별 세부 선택
    elif current_step == 2:
        subject = selections.get('subject', '')
        
        if subject == "사람":
            st.markdown("**👥 성별 선택** (클릭하면 자동 입력)")
            gender_opts = [("👨 남자", "남자"), ("👩 여자", "여자"), ("🧑 무관", "성별 무관")]
            kw_cols = st.columns(3)
            for i, (label, value) in enumerate(gender_opts):
                with kw_cols[i]:
                    if st.button(label, key=f"gender_{i}", use_container_width=True):
                        st.session_state.ai_selections['gender'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 👶 나이대를 선택해주세요."})
                        st.session_state.chat_step = 3
                        st.rerun()
                        
        elif subject == "동물":
            st.markdown("**🐾 동물 종류** (클릭하거나 직접 입력)")
            animal_opts = [("🐱 고양이", "고양이"), ("🐶 강아지", "강아지"), ("🦁 사자", "사자"), ("🐯 호랑이", "호랑이"), ("🐰 토끼", "토끼"), ("🦋 나비", "나비")]
            kw_cols = st.columns(3)
            for i, (label, value) in enumerate(animal_opts[:3]):
                with kw_cols[i]:
                    if st.button(label, key=f"animal_type_{i}", use_container_width=True):
                        st.session_state.ai_selections['animal_type'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": f"{value}! 좋아요! 🐾 성별은 어떻게 할까요?"})
                        st.session_state.chat_step = 3  # 성별 선택으로
                        st.rerun()
            kw_cols2 = st.columns(3)
            for i, (label, value) in enumerate(animal_opts[3:]):
                with kw_cols2[i]:
                    if st.button(label, key=f"animal_type_{i+3}", use_container_width=True):
                        st.session_state.ai_selections['animal_type'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": f"{value}! 좋아요! 🐾 성별은 어떻게 할까요?"})
                        st.session_state.chat_step = 3
                        st.rerun()
                        
        elif subject == "사물":
            st.markdown("**💎 사물 종류** (클릭하거나 직접 입력)")
            object_opts = [("💎 보석", "보석"), ("⌚ 시계", "시계"), ("🎸 악기", "악기"), ("🚗 자동차", "자동차"), ("📿 액세서리", "액세서리"), ("🏺 도자기", "도자기")]
            kw_cols = st.columns(3)
            for i, (label, value) in enumerate(object_opts[:3]):
                with kw_cols[i]:
                    if st.button(label, key=f"object_type_{i}", use_container_width=True):
                        st.session_state.ai_selections['object_type'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": f"{value}! 멋져요! 💎 좀 더 구체적으로 어떤 {value}인가요?\n\n예: 색상, 모양, 재질, 스타일 등을 자유롭게 설명해주세요!"})
                        st.session_state.chat_step = 4  # 세부 설명으로
                        st.rerun()
            kw_cols2 = st.columns(3)
            for i, (label, value) in enumerate(object_opts[3:]):
                with kw_cols2[i]:
                    if st.button(label, key=f"object_type_{i+3}", use_container_width=True):
                        st.session_state.ai_selections['object_type'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": f"{value}! 멋져요! 💎 좀 더 구체적으로 어떤 {value}인가요?\n\n예: 색상, 모양, 재질, 스타일 등을 자유롭게 설명해주세요!"})
                        st.session_state.chat_step = 4
                        st.rerun()
                        
        elif subject == "식물":
            st.markdown("**🌸 식물 종류** (클릭하면 자동 입력)")
            plant_opts = [("🌹 장미", "장미"), ("🌸 벚꽃", "벚꽃"), ("🌷 튤립", "튤립"), ("🌻 해바라기", "해바라기"), ("🌳 나무", "나무"), ("🌿 풀/잎", "풀과 잎")]
            kw_cols = st.columns(3)
            for i, (label, value) in enumerate(plant_opts[:3]):
                with kw_cols[i]:
                    if st.button(label, key=f"plant_{i}", use_container_width=True):
                        st.session_state.ai_selections['plant_type'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": f"{value}! 예뻐요! 🌿 식물의 양은 어느 정도로 할까요?"})
                        st.session_state.chat_step = 4
                        st.rerun()
            kw_cols2 = st.columns(3)
            for i, (label, value) in enumerate(plant_opts[3:]):
                with kw_cols2[i]:
                    if st.button(label, key=f"plant_{i+3}", use_container_width=True):
                        st.session_state.ai_selections['plant_type'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": f"{value}! 예뻐요! 🌿 식물의 양은 어느 정도로 할까요?"})
                        st.session_state.chat_step = 4
                        st.rerun()
    
    # 3단계: 사람 나이대 / 동물 성별 선택
    elif current_step == 3:
        subject = selections.get('subject', '')
        
        if subject == "사람":
            st.markdown("**👶 나이대 선택** (클릭하면 자동 입력)")
            age_opts = [("👶 어린이", "어린이"), ("🧒 청소년", "청소년"), ("👱 20대", "20대"), ("👨‍💼 30-40대", "30-40대"), ("👴 중년 이상", "중년 이상")]
            kw_cols = st.columns(5)
            for i, (label, value) in enumerate(age_opts):
                with kw_cols[i]:
                    if st.button(label, key=f"age_{i}", use_container_width=True):
                        st.session_state.ai_selections['age'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 👤 이 사람이 어떤 포즈나 행동을 하고 있으면 좋을까요?\n\n예: 서있는, 앉아있는, 걷는, 뒷모습, 옆모습 등"})
                        st.session_state.chat_step = 4  # 포즈/행동 선택
                        st.rerun()
                        
        elif subject == "동물":
            st.markdown("**🐾 성별 선택** (클릭하면 자동 입력)")
            gender_opts = [("♂️ 수컷", "수컷"), ("♀️ 암컷", "암컷"), ("🐾 무관", "성별 무관")]
            kw_cols = st.columns(3)
            for i, (label, value) in enumerate(gender_opts):
                with kw_cols[i]:
                    if st.button(label, key=f"animal_gender_{i}", use_container_width=True):
                        st.session_state.ai_selections['gender'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        animal_type = st.session_state.ai_selections.get('animal_type', '동물')
                        st.session_state.chat_messages.append({"role": "assistant", "content": f"좋아요! 🐾 이 {animal_type}가 어떤 포즈나 행동을 하고 있으면 좋을까요?\n\n예: 앉아있는, 누워있는, 뛰는, 잠자는, 정면, 옆모습 등"})
                        st.session_state.chat_step = 4  # 포즈/행동 선택
                        st.rerun()
    
    # 4단계: 포즈/행동, 식물양, 사물 세부설명
    elif current_step == 4:
        subject = selections.get('subject', '')
        
        if subject == "사람":
            st.markdown("**🧍 포즈/행동 선택** (클릭하거나 직접 입력)")
            pose_opts = [("🧍 서있는", "서있는"), ("🪑 앉아있는", "앉아있는"), ("🚶 걷는", "걷는"), ("👤 뒷모습", "뒷모습"), ("👥 옆모습", "옆모습"), ("😌 눈감은", "눈감은")]
            kw_cols = st.columns(3)
            for i, (label, value) in enumerate(pose_opts[:3]):
                with kw_cols[i]:
                    if st.button(label, key=f"pose_{i}", use_container_width=True):
                        st.session_state.ai_selections['pose'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🌤️ 배경 날씨는 어떤 느낌이 좋을까요?"})
                        st.session_state.chat_step = 5
                        st.rerun()
            kw_cols2 = st.columns(3)
            for i, (label, value) in enumerate(pose_opts[3:]):
                with kw_cols2[i]:
                    if st.button(label, key=f"pose_{i+3}", use_container_width=True):
                        st.session_state.ai_selections['pose'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🌤️ 배경 날씨는 어떤 느낌이 좋을까요?"})
                        st.session_state.chat_step = 5
                        st.rerun()
                        
        elif subject == "동물":
            st.markdown("**🐾 포즈/행동 선택** (클릭하거나 직접 입력)")
            pose_opts = [("🐱 앉아있는", "앉아있는"), ("😴 누워있는", "누워있는"), ("🏃 뛰는", "뛰는"), ("😺 정면", "정면"), ("🐈 옆모습", "옆모습"), ("💤 잠자는", "잠자는")]
            kw_cols = st.columns(3)
            for i, (label, value) in enumerate(pose_opts[:3]):
                with kw_cols[i]:
                    if st.button(label, key=f"animal_pose_{i}", use_container_width=True):
                        st.session_state.ai_selections['pose'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🌤️ 배경 날씨는 어떤 느낌이 좋을까요?"})
                        st.session_state.chat_step = 5
                        st.rerun()
            kw_cols2 = st.columns(3)
            for i, (label, value) in enumerate(pose_opts[3:]):
                with kw_cols2[i]:
                    if st.button(label, key=f"animal_pose_{i+3}", use_container_width=True):
                        st.session_state.ai_selections['pose'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🌤️ 배경 날씨는 어떤 느낌이 좋을까요?"})
                        st.session_state.chat_step = 5
                        st.rerun()
                        
        elif subject == "사물":
            # 사물은 직접 입력 유도 (버튼 없이 대화로)
            st.caption("💡 위 입력창에 원하는 사물의 특징을 자유롭게 설명해주세요!")
            st.caption("예: 빨간색 루비, 금색 테두리의 시계, 우아한 바이올린 등")
                        
        elif subject == "식물":
            st.markdown("**🌿 식물의 양** (클릭하면 자동 입력)")
            amount_opts = [("🌱 조금", "조금만"), ("🌿 적당히", "적당히"), ("🌳 많이", "많이"), ("🌲 가득", "가득 채워서")]
            kw_cols = st.columns(4)
            for i, (label, value) in enumerate(amount_opts):
                with kw_cols[i]:
                    if st.button(label, key=f"amount_{i}", use_container_width=True):
                        st.session_state.ai_selections['amount'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🌤️ 배경 날씨는 어떤 느낌이 좋을까요?"})
                        st.session_state.chat_step = 5
                        st.rerun()
    
    # 5단계: 날씨 선택 (흐림/맑음)
    elif current_step == 5:
        st.markdown("**🌤️ 날씨 선택** (클릭하면 자동 입력)")
        weather_opts = [("☁️ 흐림", "흐린 날씨"), ("☀️ 맑음", "맑은 날씨")]
        kw_cols = st.columns(2)
        for i, (label, value) in enumerate(weather_opts):
            with kw_cols[i]:
                if st.button(label, key=f"weather_{i}", use_container_width=True):
                    st.session_state.ai_selections['weather'] = value
                    st.session_state.chat_messages.append({"role": "user", "content": value})
                    st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🌙 낮인가요 밤인가요?"})
                    st.session_state.chat_step = 6
                    st.rerun()
    
    # 6단계: 시간대 선택 (낮/밤)
    elif current_step == 6:
        st.markdown("**🌙 시간대 선택** (클릭하면 자동 입력)")
        time_opts = [("☀️ 낮", "낮"), ("🌙 밤", "밤")]
        kw_cols = st.columns(2)
        for i, (label, value) in enumerate(time_opts):
            with kw_cols[i]:
                if st.button(label, key=f"time_{i}", use_container_width=True):
                    st.session_state.ai_selections['time'] = value
                    st.session_state.chat_messages.append({"role": "user", "content": value})
                    st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! ✨ 배경 요소를 선택해주세요. (여러 개 선택 가능)"})
                    st.session_state.chat_step = 7
                    # 다중 선택을 위한 초기화
                    if 'bg_elements' not in st.session_state.ai_selections:
                        st.session_state.ai_selections['bg_elements'] = []
                    st.rerun()
    
    # 7단계: 배경 요소 선택 (중복 선택 가능)
    elif current_step == 7:
        st.markdown("**✨ 배경 요소** (여러 개 선택 가능, 완료 후 '선택 완료' 클릭)")
        
        bg_elements = [
            ("☁️ 구름", "구름"),
            ("☀️ 해", "해"),
            ("🌙 달", "달"),
            ("⭐ 별", "별"),
            ("🌧️ 비", "비")
        ]
        
        # 현재 선택된 요소들
        selected_elements = st.session_state.ai_selections.get('bg_elements', [])
        
        kw_cols = st.columns(5)
        for i, (label, value) in enumerate(bg_elements):
            with kw_cols[i]:
                is_selected = value in selected_elements
                btn_type = "primary" if is_selected else "secondary"
                if st.button(label, key=f"bg_elem_{i}", use_container_width=True, type=btn_type):
                    if value in selected_elements:
                        selected_elements.remove(value)
                    else:
                        selected_elements.append(value)
                    st.session_state.ai_selections['bg_elements'] = selected_elements
                    st.rerun()
        
        # 선택 완료 버튼
        st.write("")
        if st.button("✅ 선택 완료", use_container_width=True, type="primary"):
            elements_text = ", ".join(selected_elements) if selected_elements else "없음"
            st.session_state.chat_messages.append({"role": "user", "content": f"배경 요소: {elements_text}"})
            st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🎨 마지막으로 전체 분위기를 선택해주세요."})
            st.session_state.chat_step = 8
            st.rerun()
    
    # 8단계: 분위기 선택
    elif current_step >= 8 and current_step < 10:
        st.markdown("**🎨 분위기 선택** (클릭하면 자동 입력)")
        mood_opts = [("✨ 우아한", "우아한"), ("🔮 신비로운", "신비로운"), ("💧 청량한", "청량한"), ("🔥 따뜻한", "따뜻한"), ("👑 고급스러운", "고급스러운"), ("📜 빈티지한", "빈티지한")]
        
        # 2행 3열로 배치
        row1 = st.columns(3)
        row2 = st.columns(3)
        
        for i, (label, value) in enumerate(mood_opts[:3]):
            with row1[i]:
                if st.button(label, key=f"mood_{i}", use_container_width=True):
                    st.session_state.ai_selections['mood'] = value
                    st.session_state.chat_messages.append({"role": "user", "content": f"{value} 분위기로 해주세요"})
                    st.session_state.chat_messages.append({"role": "assistant", "content": f"완벽해요! ✨ 모든 선택이 완료되었습니다.\n\n👉 '이미지 생성' 버튼을 눌러주세요!"})
                    st.session_state.chat_step = 10
                    st.rerun()
        
        for i, (label, value) in enumerate(mood_opts[3:]):
            with row2[i]:
                if st.button(label, key=f"mood_{i+3}", use_container_width=True):
                    st.session_state.ai_selections['mood'] = value
                    st.session_state.chat_messages.append({"role": "user", "content": f"{value} 분위기로 해주세요"})
                    st.session_state.chat_messages.append({"role": "assistant", "content": f"완벽해요! ✨ 모든 선택이 완료되었습니다.\n\n👉 '이미지 생성' 버튼을 눌러주세요!"})
                    st.session_state.chat_step = 10
                    st.rerun()
    
    st.write("")
    
    # 하단 버튼
    col_reset, col_generate = st.columns(2)
    with col_reset:
        if st.button("대화 초기화", use_container_width=True, type="secondary"):
            st.session_state.chat_messages = [
                {"role": "assistant", "content": "안녕하세요! 라벨에 어떤 주제를 담고 싶으신가요? 🎨\n\n아래에서 선택하거나 직접 입력해주세요!"}
            ]
            st.session_state.chat_step = 1
            st.session_state.ai_selections = {}
            st.rerun()
    with col_generate:
        if st.button("이미지 생성", use_container_width=True, type="primary"):
            # 채팅 내용에서 프롬프트 추출
            user_messages = [m["content"] for m in st.session_state.chat_messages if m["role"] == "user"]
            if user_messages:
                final_prompt = " ".join(user_messages[-3:])  # 최근 3개 사용자 메시지
                st.session_state.form_data['ai_prompt'] = final_prompt
                st.session_state.ai_generating = True
                st.session_state.show_ai_dialog = False
                st.session_state.show_ai_result = True
                st.rerun()
            else:
                st.warning("먼저 원하는 느낌을 설명해주세요!")

# --- 페이지 설정 ---
st.set_page_config(layout="wide", page_title="Perfume Label Studio V2")

# --- 세션 상태 초기화 ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'temp_saved' not in st.session_state:
    st.session_state.temp_saved = False

# --- API 설정 (환경 변수에서 안전하게 로드) ---
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    st.stop()
client = OpenAI(api_key=api_key)

# --- 스타일 CSS ---
st.markdown("""
<style>
    /* 상단 헤더 바 */
    .header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 20px;
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .header-title {
        color: white;
        font-size: 18px;
        font-weight: 600;
    }
    .header-buttons {
        display: flex;
        gap: 10px;
    }
    
    /* 단계 표시 바 */
    .step-container {
        display: flex;
        justify-content: center;
        margin: 30px 0;
    }
    .step-item {
        text-align: center;
        padding: 0 30px;
        position: relative;
    }
    .step-item:not(:last-child)::after {
        content: '';
        position: absolute;
        top: 15px;
        right: -15px;
        width: 30px;
        height: 2px;
        background: #ddd;
    }
    .step-number {
        font-size: 14px;
        font-weight: 600;
        color: #666;
    }
    .step-number.active {
        color: #3d5afe;
    }
    .step-label {
        font-size: 12px;
        color: #999;
        margin-top: 5px;
    }
    .step-label.active {
        color: #3d5afe;
    }
    
    /* 하단 네비게이션 */
    .bottom-nav {
        display: flex;
        justify-content: center;
        margin-top: 40px;
        padding: 20px;
    }
    
    /* 단계 네비게이션 버튼 스타일 - 링크처럼 */
    .step-nav-container button {
        background: none !important;
        border: none !important;
        box-shadow: none !important;
        font-weight: 600 !important;
        padding: 5px !important;
    }
    .step-nav-container button:hover {
        background: none !important;
        text-decoration: underline !important;
    }
    .step-nav-container button:focus {
        box-shadow: none !important;
    }
    
    /* file_uploader 버튼 스타일 - AI로 생성 버튼과 동일 */
    [data-testid="stFileUploader"] {
        width: 100%;
    }
    [data-testid="stFileUploader"] section {
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 0;
    }
    [data-testid="stFileUploader"] section > input + div {
        display: none !important;
    }
    [data-testid="stFileUploader"] section > button {
        width: 100%;
        background-color: rgb(255, 255, 255) !important;
        color: rgb(49, 51, 63) !important;
        border: 1px solid rgba(49, 51, 63, 0.2) !important;
        padding: 0.5rem 1rem !important;
        border-radius: 0.5rem !important;
        font-weight: 400 !important;
        text-align: center !important;
        margin-bottom: 8px !important;
        font-size: 0 !important;
    }
    [data-testid="stFileUploader"] section > button::after {
        content: "이미지 업로드";
        font-size: 14px !important;
    }
    [data-testid="stFileUploader"] section > button:hover {
        border-color: rgb(49, 51, 63) !important;
    }
    [data-testid="stFileUploader"] small {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 함수 정의 ---
def go_next():
    if st.session_state.step < 4:
        # 2단계에서 "단색 배경" 선택 시 3단계 스킵
        if st.session_state.step == 2:
            art_style = st.session_state.form_data.get('art_style', '단색 배경')
            if art_style == '단색 배경':
                st.session_state.step = 4  # 바로 최종 단계로
                return
        st.session_state.step += 1

def go_prev():
    if st.session_state.step > 1:
        # 4단계에서 이전 버튼 시, "단색 배경"이면 2단계로
        if st.session_state.step == 4:
            art_style = st.session_state.form_data.get('art_style', '단색 배경')
            if art_style == '단색 배경':
                st.session_state.step = 2
                return
        st.session_state.step -= 1

def temp_save():
    st.session_state.temp_saved = True
    st.toast("✅ 임시 저장되었습니다!")

def reset_form():
    st.session_state.step = 1
    st.session_state.form_data = {}
    st.session_state.temp_saved = False

# --- 상단 헤더 바 ---
header_col1, header_col2, header_col3 = st.columns([2, 4, 2])

with header_col1:
    if st.button("라벨 만들기", key="title_btn", type="tertiary"):
        reset_form()
        st.rerun()

with header_col3:
    col_temp, col_gen = st.columns(2)
    with col_temp:
        if st.button("임시저장", key="temp_save_btn", use_container_width=True):
            temp_save()
    with col_gen:
        if st.button("생성", key="generate_btn", type="primary", use_container_width=True):
            st.session_state.step = 4

st.write("")

# --- 단계 표시 바 (중앙 정렬) ---
step_center_col1, step_center_col2, step_center_col3 = st.columns([1, 3, 1])

with step_center_col2:
    # 단계 네비게이션 컨테이너 시작
    st.markdown('<div class="step-nav-container">', unsafe_allow_html=True)
    
    step_cols = st.columns(4)
    
    steps_info = [
        ("1단계", "기본 설정"),
        ("2단계", "상세 설정"),
        ("3단계", "라벨 이미지"),
        ("최종", "마무리 설정")
    ]
    
    for i, (step_num, step_label) in enumerate(steps_info):
        with step_cols[i]:
            is_active = st.session_state.step >= (i + 1)
            is_current = st.session_state.step == (i + 1)
            text_color = "#FFD700" if is_current else ("#aaa" if is_active else "#666")
            
            # 클릭 가능한 텍스트
            if st.button(step_num, key=f"step_nav_{i}a", use_container_width=True, type="tertiary"):
                st.session_state.step = i + 1
                st.rerun()
            st.markdown(f"<p style='text-align:center; color:{text_color}; font-size:12px; margin-top:-10px;'>{step_label}</p>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 노란색 게이지 바 (현재 단계까지만)
    progress_html = f"""
    <div style="display: flex; margin-top: 5px;">
        <div style="flex: 1; height: 3px; background: {'#FFD700' if st.session_state.step >= 1 else '#333'}; margin-right: 2px;"></div>
        <div style="flex: 1; height: 3px; background: {'#FFD700' if st.session_state.step >= 2 else '#333'}; margin-right: 2px;"></div>
        <div style="flex: 1; height: 3px; background: {'#FFD700' if st.session_state.step >= 3 else '#333'}; margin-right: 2px;"></div>
        <div style="flex: 1; height: 3px; background: {'#FFD700' if st.session_state.step >= 4 else '#333'};"></div>
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)

st.write("")
st.write("")

# --- 단계별 콘텐츠 ---
content_col1, content_col2, content_col3 = st.columns([1, 2, 1])

with content_col2:
    
    # ==================== 1단계: 기본 설정 ====================
    if st.session_state.step == 1:
        
        # 브랜드 이름
        brand_col1, brand_col2 = st.columns([4, 1])
        with brand_col1:
            st.markdown("**브랜드 이름** *")
        with brand_col2:
            brand_count = len(st.session_state.form_data.get('brand_name', ''))
            st.markdown(f"<p style='text-align:right; color:#888; font-size:12px;'>{brand_count}/20</p>", unsafe_allow_html=True)
        brand_name = st.text_input(
            "브랜드 이름", 
            value=st.session_state.form_data.get('brand_name', ''),
            max_chars=20,
            placeholder="브랜드 이름을 입력해 주세요.",
            label_visibility="collapsed"
        )
        
        # 향수 이름
        perfume_col1, perfume_col2 = st.columns([4, 1])
        with perfume_col1:
            st.markdown("**향수 이름** *")
        with perfume_col2:
            perfume_count = len(st.session_state.form_data.get('perfume_name', ''))
            st.markdown(f"<p style='text-align:right; color:#888; font-size:12px;'>{perfume_count}/20</p>", unsafe_allow_html=True)
        perfume_name = st.text_input(
            "향수 이름",
            value=st.session_state.form_data.get('perfume_name', ''),
            max_chars=20,
            placeholder="향수 이름을 입력해 주세요.",
            label_visibility="collapsed"
        )
        
        # 셀럽 이름
        celeb_col1, celeb_col2 = st.columns([4, 1])
        with celeb_col1:
            st.markdown("**셀럽 이름 / 문구**")
        with celeb_col2:
            celeb_count = len(st.session_state.form_data.get('celeb_name', ''))
            st.markdown(f"<p style='text-align:right; color:#888; font-size:12px;'>{celeb_count}/20</p>", unsafe_allow_html=True)
        celeb_name = st.text_input(
            "셀럽 이름 / 문구",
            value=st.session_state.form_data.get('celeb_name', ''),
            max_chars=20,
            placeholder="예: Designed by V",
            label_visibility="collapsed"
        )
        
        # 저장
        st.session_state.form_data['brand_name'] = brand_name
        st.session_state.form_data['perfume_name'] = perfume_name
        st.session_state.form_data['celeb_name'] = celeb_name
    
    # ==================== 2단계: 상세 설정 ====================
    elif st.session_state.step == 2:
        st.markdown("라벨의 스타일과 색상을 설정해주세요.")
        st.write("")
        
        # 향의 분위기 - 박스 선택 (중복 가능)
        st.markdown("**향의 전체적인 분위기** * (중복 선택 가능)")
        
        # 선택 상태 초기화
        if 'selected_vibes' not in st.session_state.form_data:
            st.session_state.form_data['selected_vibes'] = []
        
        vibe_options = ["청량한", "우아한", "신비로운", "강렬한", "따뜻한", "달콤한", "상쾌한", "차분한", "관능적인"]
        
        # 3열로 배치
        vibe_cols = st.columns(3)
        for idx, vibe in enumerate(vibe_options):
            with vibe_cols[idx % 3]:
                is_selected = vibe in st.session_state.form_data['selected_vibes']
                btn_type = "primary" if is_selected else "secondary"
                if st.button(
                    f"{'✓ ' if is_selected else ''}{vibe}", 
                    key=f"vibe_{vibe}",
                    type=btn_type,
                    use_container_width=True
                ):
                    if is_selected:
                        st.session_state.form_data['selected_vibes'].remove(vibe)
                    else:
                        st.session_state.form_data['selected_vibes'].append(vibe)
                    st.rerun()
        
        st.write("")
        
        # 담고 싶은 분위기/기억
        memory_col1, memory_col2 = st.columns([4, 1])
        with memory_col1:
            st.markdown("**담고 싶은 분위기/기억** *")
        with memory_col2:
            memory_count = len(st.session_state.form_data.get('memory', ''))
            st.markdown(f"<p style='text-align:right; color:#888; font-size:12px;'>{memory_count}/1000</p>", unsafe_allow_html=True)
        
        memory = st.text_area(
            "담고 싶은 분위기/기억",
            value=st.session_state.form_data.get('memory', ''),
            max_chars=1000,
            placeholder="예: 깊은 밤, 달빛이 비추는 조용한 바다와 은은한 우드 향",
            height=120,
            label_visibility="collapsed"
        )
        
        st.write("")
        
        # 아트 스타일 (버튼 선택)
        st.markdown("**아트 스타일**")
        
        art_styles = [
            ("단색 배경", "단색 배경", None),
            ("그라디언트", "Minimal Gradient (그라데이션)", None),
            ("유화", "Oil Painting (유화)", "style_oil.png"),
            ("수채화", "Watercolor (수채화)", "style_watercolor.png"),
            ("신표현주의", "Abstract (추상화)", "style_abstract.png"),
            ("포토그래피", "Photography (포토그래피)", "style_photo.png")
        ]
        
        # 기본값 None (선택 안됨)
        current_style = st.session_state.form_data.get('art_style', None)
        
        # 1행: 단색 배경, 그라디언트 (2열)
        row1_cols = st.columns(2)
        for i in range(2):
            label, value, img = art_styles[i]
            with row1_cols[i]:
                is_selected = current_style == value
                if st.button(
                    label,
                    key=f"art_style_{i}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.form_data['art_style'] = value
                    st.rerun()
        
        # 2행: 유화, 수채화 (2열) - 썸네일 미리보기 포함
        row2_cols = st.columns(2)
        for i in range(2, 4):
            label, value, img = art_styles[i]
            with row2_cols[i - 2]:
                is_selected = current_style == value
                
                # 썸네일 미리보기 이미지
                if img:
                    img_path = os.path.join(os.path.dirname(__file__), "static", img)
                    if os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                
                if st.button(
                    label,
                    key=f"art_style_{i}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.form_data['art_style'] = value
                    st.rerun()
        
        # 3행: 신표현주의, 포토그래피 (2열) - 썸네일 미리보기 포함
        row3_cols = st.columns(2)
        for i in range(4, 6):
            label, value, img = art_styles[i]
            with row3_cols[i - 4]:
                is_selected = current_style == value
                
                # 썸네일 미리보기 이미지
                if img:
                    img_path = os.path.join(os.path.dirname(__file__), "static", img)
                    if os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                
                if st.button(
                    label,
                    key=f"art_style_{i}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.form_data['art_style'] = value
                    st.rerun()
        
        art_style = st.session_state.form_data.get('art_style', None)
        
        st.write("")
        
        # 폰트 선택
        st.markdown("**폰트 선택**")
        
        # 웹폰트 로드 (Google Fonts + 로컬 폰트)
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');
        @font-face {
            font-family: 'BagelFatOne';
            src: url('BagelFatOne_Regular_font.ttf') format('truetype');
        }
        @font-face {
            font-family: 'SCDream';
            src: url('SCDream9_font.otf') format('opentype');
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 폰트 옵션
        font_options = [
            ("Playfair", "font.ttf", "Playfair Display, serif"),
            ("BagelFatOne", "BagelFatOne_Regular_font.ttf", "BagelFatOne, sans-serif"),
            ("SCDream", "SCDream9_font.otf", "SCDream, sans-serif")
        ]
        
        current_font = st.session_state.form_data.get('selected_font', 'font.ttf')
        
        # 폰트 버튼들 (각 폰트 스타일 적용)
        font_cols = st.columns(3)
        for i, (font_name, font_file, font_css) in enumerate(font_options):
            with font_cols[i]:
                is_selected = current_font == font_file
                border_color = "#FFD700" if is_selected else "#555"
                bg_color = "#2a2a2a" if is_selected else "#1a1a1a"
                
                # HTML 버튼으로 폰트 스타일 적용
                st.markdown(f"""
                <div style="width: 100%; padding: 10px; background: {bg_color}; 
                     border: 2px solid {border_color}; border-radius: 8px; 
                     text-align: center; cursor: pointer; margin-bottom: 5px;">
                    <span style="font-family: {font_css}; font-size: 16px; color: white;">{font_name}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("선택" if not is_selected else "✓ 선택됨", key=f"font_btn_{i}", use_container_width=True, type="primary" if is_selected else "secondary"):
                    st.session_state.form_data['selected_font'] = font_file
                    st.rerun()
        
        # 향수 이름 미리보기 (선택된 폰트 적용)
        perfume_name = st.session_state.form_data.get('perfume_name', 'Perfume Name')
        
        # 현재 선택된 폰트의 CSS
        current_font_css = "Playfair Display, serif"
        for font_name, font_file, font_css in font_options:
            if font_file == current_font:
                current_font_css = font_css
                break
        
        st.markdown(f"""
        <div style="width: 100%; height: 70px; background: #333;
             border-radius: 8px; border: 1px solid #555;
             display: flex; align-items: center; justify-content: center; margin-top: 10px;">
            <span style="font-family: {current_font_css}; color: #FFFFFF; font-size: 22px; font-weight: bold;">{perfume_name.upper()}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption("👁️ 1단계에서 입력한 향수 이름 미리보기 (선택한 폰트 적용)")
        
        st.write("")
        
        # 색상 설정 - 단색 배경 선택 시에만 펼쳐짐
        is_solid_bg = art_style == "단색 배경"
        with st.expander("🎨 색상 설정", expanded=is_solid_bg):
            if is_solid_bg:
                # 투명 상태 초기화
                if 'no_bg' not in st.session_state.form_data:
                    st.session_state.form_data['no_bg'] = False
                
                no_bg = st.session_state.form_data.get('no_bg', False)
                current_bg = st.session_state.form_data.get('bg_color', '#000000')
                current_text = st.session_state.form_data.get('text_color', '#FFFFFF')
                
                # 색상 선택 (3열: 투명, 배경색, 텍스트색)
                color_cols = st.columns([1, 1, 1])
                
                with color_cols[0]:
                    st.markdown("투명 배경")
                    is_transparent = st.session_state.form_data.get('no_bg', False)
                    
                    # PIL로 체크 패턴 이미지 생성 (32x32)
                    check_size = 32
                    check_img = Image.new('RGBA', (check_size, check_size), (255, 255, 255, 255))
                    for y in range(check_size):
                        for x in range(check_size):
                            if (x // 4 + y // 4) % 2 == 0:
                                check_img.putpixel((x, y), (180, 180, 180, 255))
                    
                    # 선택 시 테두리 추가
                    if is_transparent:
                        draw = ImageDraw.Draw(check_img)
                        draw.rectangle([0, 0, check_size-1, check_size-1], outline=(255, 215, 0), width=3)
                    
                    # 모노체크 이미지 표시
                    st.image(check_img, width=38)
                    
                    # 토글로 선택
                    new_val = st.toggle("선택", value=is_transparent, key="transparent_toggle")
                    if new_val != is_transparent:
                        st.session_state.form_data['no_bg'] = new_val
                        st.rerun()
                
                with color_cols[1]:
                    st.markdown("배경 색상")
                    # 투명 배경 선택 시 비활성화
                    if st.session_state.form_data.get('no_bg', False):
                        st.markdown("""
                        <div style="width: 38px; height: 38px; background: #ccc; border-radius: 4px; 
                             display: flex; align-items: center; justify-content: center; color: #888;">
                            -
                        </div>
                        """, unsafe_allow_html=True)
                        st.caption("투명 선택됨")
                    else:
                        bg_color = st.color_picker(
                            "배경색",
                            value=current_bg if current_bg else '#000000',
                            label_visibility="collapsed"
                        )
                        if bg_color != current_bg:
                            st.session_state.form_data['bg_color'] = bg_color
                            st.session_state.form_data['no_bg'] = False
                
                with color_cols[2]:
                    st.markdown("텍스트 색상")
                    text_color = st.color_picker(
                        "텍스트색",
                        value=current_text,
                        label_visibility="collapsed"
                    )
                    st.session_state.form_data['text_color'] = text_color
                
                st.write("")
                
                # 통합 미리보기 창
                st.markdown("**미리보기**")
                preview_text = st.session_state.form_data.get('text_color', '#FFFFFF')
                
                if st.session_state.form_data.get('no_bg', False):
                    st.markdown(f"""
                    <div style="width: 100%; height: 80px;
                         background: repeating-conic-gradient(#ccc 0% 25%, #fff 0% 50%) 50% / 10px 10px;
                         border-radius: 8px; border: 1px solid #ddd;
                         display: flex; align-items: center; justify-content: center;">
                        <span style="color: {preview_text}; font-size: 18px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">Sample Text</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="width: 100%; height: 80px; background: {st.session_state.form_data.get('bg_color', '#000000')};
                         border-radius: 8px; border: 1px solid #ddd;
                         display: flex; align-items: center; justify-content: center;">
                        <span style="color: {preview_text}; font-size: 18px; font-weight: bold;">Sample Text</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.caption("💡 색상 박스를 클릭하면 포토샵처럼 자유롭게 색상을 선택할 수 있습니다.")
            else:
                # 단색이 아닌 경우 텍스트 색상만 설정
                st.markdown("**텍스트 색상**")
                current_text = st.session_state.form_data.get('text_color', '#FFFFFF')
                text_color = st.color_picker(
                    "텍스트색",
                    value=current_text,
                    label_visibility="collapsed"
                )
                st.session_state.form_data['text_color'] = text_color
                st.caption("💡 AI 이미지 위에 표시될 텍스트 색상입니다.")
        
        # 저장
        st.session_state.form_data['memory'] = memory
    
    # ==================== 3단계: 라벨 이미지 ====================
    elif st.session_state.step == 3:
        st.markdown("**라벨 이미지** *")
        st.caption("타인의 이미지를 무단으로 도용할 경우 법적인 처벌을 받을 수 있습니다.")
        st.write("")
        
        # 이미지 리스트 초기화
        if 'label_images' not in st.session_state.form_data:
            st.session_state.form_data['label_images'] = []
        if 'selected_image_idx' not in st.session_state.form_data:
            st.session_state.form_data['selected_image_idx'] = None
        
        label_images = st.session_state.form_data['label_images']
        max_images = 2
        uploaded_count = len(label_images)
        
        # 표시할 박스 수 결정 (이미지가 없으면 1개, 있으면 이미지 수 + 1, 최대 2개)
        display_count = 1 if uploaded_count == 0 else min(uploaded_count + 1, max_images)
        
        # 이미지 박스들 표시 (컬럼을 더 작게)
        col_spacer1, col_images, col_spacer2 = st.columns([1, 2, 1])
        
        with col_images:
            img_cols = st.columns(display_count)
            
            for i in range(display_count):
                with img_cols[i]:
                    if i < uploaded_count:
                        # 생성된 이미지 표시
                        is_selected = st.session_state.form_data.get('selected_image_idx') == i
                        border_color = "#FFD700" if is_selected else "#333"
                        border_width = "3px" if is_selected else "1px"
                        
                        # PIL Image인 경우와 UploadedFile인 경우 구분
                        img_data = label_images[i]
                        st.image(img_data, use_container_width=True)
                        
                        # 선택 버튼
                        btn_label = "✓ 선택됨" if is_selected else "선택"
                        btn_type = "primary" if is_selected else "secondary"
                        if st.button(btn_label, key=f"select_img_{i}", use_container_width=True, type=btn_type):
                            st.session_state.form_data['selected_image_idx'] = i
                            st.rerun()
                    
                    elif i == uploaded_count and uploaded_count < max_images:
                        # 빈 박스 (업로드/생성 가능)
                        st.markdown(f"""
                        <div style="width: 100%; aspect-ratio: 1; background: #1a1a1a; border-radius: 8px;
                             display: flex; flex-direction: column; align-items: center; justify-content: center;
                             border: 1px solid #333; max-width: 200px;">
                            <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="1.5">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                <circle cx="8.5" cy="8.5" r="1.5"/>
                                <polyline points="21 15 16 10 5 21"/>
                            </svg>
                            <span style="color: #666; font-size: 14px; margin-top: 10px;">{uploaded_count}/{max_images}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.write("")
                        
                        # AI로 생성 버튼만
                        if st.button("AI로 생성", use_container_width=True, type="secondary", key=f"ai_gen_{uploaded_count}"):
                            st.session_state.show_ai_dialog = True
                            st.rerun()
        
        # AI 키워드 입력 모달 표시
        if st.session_state.get('show_ai_dialog'):
            ai_image_dialog()
        
        # AI 이미지 결과 모달 표시
        if st.session_state.get('show_ai_result'):
            ai_image_result_dialog()
            st.session_state.show_ai_result = False
        
        st.write("")
        st.write("")
        
        label_opacity = st.slider(
            "라벨 투명도 (%)",
            min_value=50,
            max_value=100,
            value=st.session_state.form_data.get('label_opacity', 95)
        )
        
        st.write("")
        
        # 로고 색상 선택
        st.markdown("**로고 색상**")
        logo_color = st.session_state.form_data.get('logo_color', 'white')
        logo_cols = st.columns(2)
        with logo_cols[0]:
            is_white = logo_color == 'white'
            if st.button("⬜ 흰색 로고", key="logo_white", use_container_width=True, type="primary" if is_white else "secondary"):
                st.session_state.form_data['logo_color'] = 'white'
                st.rerun()
        with logo_cols[1]:
            is_black = logo_color == 'black'
            if st.button("⬛ 검정 로고", key="logo_black", use_container_width=True, type="primary" if is_black else "secondary"):
                st.session_state.form_data['logo_color'] = 'black'
                st.rerun()
        
        # 저장
        st.session_state.form_data['label_opacity'] = label_opacity
    
    # ==================== 최종: 미리보기 및 생성 ====================
    elif st.session_state.step == 4:
        st.markdown("### 최종 미리보기")
        st.markdown("설정을 확인하고 라벨을 생성하세요.")
        st.write("")
        
        # 설정 요약 표시
        with st.expander("📋 설정 요약", expanded=True):
            col_sum1, col_sum2 = st.columns(2)
            with col_sum1:
                st.write(f"**브랜드:** {st.session_state.form_data.get('brand_name', '-')}")
                st.write(f"**향수 이름:** {st.session_state.form_data.get('perfume_name', '-')}")
                st.write(f"**셀럽/문구:** {st.session_state.form_data.get('celeb_name', '-')}")
            with col_sum2:
                st.write(f"**분위기:** {st.session_state.form_data.get('scent_vibe', '-')}")
                st.write(f"**스타일:** {st.session_state.form_data.get('art_style', '-')}")
        
        st.write("")
        
        # 라벨 생성 버튼
        if st.button("✨ 라벨 생성하기", type="primary", use_container_width=True):
            with st.spinner('AI가 라벨을 디자인 중입니다...'):
                try:
                    # 데이터 가져오기
                    data = st.session_state.form_data
                    
                    # 라벨 크기 설정 (세로로 더 긴 비율 - 공병에 맞춤)
                    W, H = 600, 1250  # 세로로 더 긴 라벨
                    
                    # 배경 색상 또는 투명 배경
                    no_bg = data.get('no_bg', False)
                    if no_bg:
                        base_label_img = Image.new('RGBA', (W, H), color=(0, 0, 0, 0))
                    else:
                        bg_color = data.get('bg_color', '#1a5f7a')
                        base_label_img = Image.new('RGBA', (W, H), color=bg_color)
                    
                    # 로고 색상에 따른 텍스트 색상 자동 설정
                    logo_color = data.get('logo_color', 'white')
                    text_color = '#FFFFFF' if logo_color == 'white' else '#000000'
                    
                    # 선택된 라벨 이미지 가져오기
                    label_images = data.get('label_images', [])
                    selected_idx = data.get('selected_image_idx')
                    
                    label_art = None
                    if label_images and selected_idx is not None and selected_idx < len(label_images):
                        selected_img = label_images[selected_idx]
                        if hasattr(selected_img, 'read'):
                            label_art = Image.open(selected_img).convert("RGBA")
                        else:
                            label_art = selected_img.convert("RGBA")
                    
                    # === 배경 이미지 합성 (전체 배경으로, 단일 이미지만) ===
                    if label_art:
                        # 이미지를 라벨 전체 크기로 맞춤 (cover 방식)
                        img_w, img_h = label_art.size
                        scale = max(W / img_w, H / img_h)
                        new_w = int(img_w * scale)
                        new_h = int(img_h * scale)
                        art_resized = label_art.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        left = (new_w - W) // 2
                        top = (new_h - H) // 2
                        art_cropped = art_resized.crop((left, top, left + W, top + H))
                        base_label_img.paste(art_cropped, (0, 0), art_cropped)
                    
                    draw = ImageDraw.Draw(base_label_img)
                    
                    # === 텍스트 영역 (하단 끝자락) ===
                    # 선택된 폰트 로드
                    selected_font = data.get('selected_font', 'font.ttf')
                    try:
                        title_font = ImageFont.truetype(selected_font, 48)
                        sub_font = ImageFont.truetype(selected_font, 16)
                    except:
                        try:
                            title_font = ImageFont.truetype("font.ttf", 48)
                            sub_font = ImageFont.truetype("font.ttf", 16)
                        except:
                            try:
                                title_font = ImageFont.truetype("arial.ttf", 48)
                                sub_font = ImageFont.truetype("arial.ttf", 16)
                            except:
                                title_font = ImageFont.load_default()
                                sub_font = ImageFont.load_default()
                    
                    # 향수 이름 (하단 끝자락, 두 줄로 분리 가능)
                    perfume_name = data.get('perfume_name', 'PERFUME')
                    text_x = int(W * 0.06)  # 좌측 여백 6%
                    bottom_margin = int(H * 0.025)  # 하단 여백 2.5% (로고/50ml 더 아래로)
                    
                    # 이름이 길면 두 줄로 분리
                    name_parts = perfume_name.upper().split()
                    if len(name_parts) >= 2:
                        line1 = ' '.join(name_parts[:len(name_parts)//2])
                        line2 = ' '.join(name_parts[len(name_parts)//2:])
                        # 하단에서 위로 계산
                        info_y = H - bottom_margin - 20  # Perfume 50ml 위치 (더 아래)
                        text_y = info_y - 50 - 50 - 30  # 두 줄 이름 시작 위치 (더 위로)
                        draw.text((text_x, text_y), line1, font=title_font, fill=text_color)
                        draw.text((text_x, text_y + 50), line2, font=title_font, fill=text_color)
                    else:
                        info_y = H - bottom_margin - 20  # Perfume 50ml 위치 (더 아래)
                        text_y = info_y - 55 - 30  # 한 줄 이름 위치 (더 위로)
                        draw.text((text_x, text_y), perfume_name.upper(), font=title_font, fill=text_color)
                    
                    # "Perfume 50ml" 텍스트 (하단 끝자락)
                    draw.text((text_x, info_y), "Perfume 50ml", font=sub_font, fill=text_color)
                    
                    # === 브랜드 로고 (하단 우측 끝자락) ===
                    try:
                        logo_file = "logo_W.png" if logo_color == 'white' else "logo.png"
                        company_logo = Image.open(logo_file).convert("RGBA")
                        
                        # 로고 크기 (너비 기준 20%)
                        logo_size_percent = 20
                        target_logo_w = int(W * (logo_size_percent / 100))
                        original_w, original_h = company_logo.size
                        aspect_ratio = original_h / original_w
                        target_logo_h = int(target_logo_w * aspect_ratio)
                        
                        logo_resized = company_logo.resize((target_logo_w, target_logo_h), Image.Resampling.LANCZOS)
                        
                        # 하단 우측 끝자락 위치
                        logo_x = W - target_logo_w - int(W * 0.06)  # 우측에서 6% 여백
                        logo_y = info_y - int(target_logo_h * 0.3)  # Perfume 50ml과 같은 높이
                        
                        base_label_img.paste(logo_resized, (logo_x, logo_y), logo_resized)
                    except FileNotFoundError:
                        pass
                    
                    # 라벨 표시
                    st.image(base_label_img, caption="생성된 라벨", width=300)
                    
                    # 공병 합성
                    st.markdown("---")
                    st.markdown("#### 🧴 제품 목업")
                    
                    try:
                        bottle_img = Image.open("bottle_mockup.png").convert("RGBA")
                        bottle_w, bottle_h = bottle_img.size
                        
                        # 라벨 크기를 공병에 맞춤 (비율 유지, 더 크게)
                        target_width = int(bottle_w * 0.93)
                        target_height = int(target_width * (H / W))
                        label_resized = base_label_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                        
                        alpha = int(255 * (data.get('label_opacity', 95) / 100))
                        label_resized.putalpha(alpha)
                        
                        label_x = (bottle_w - target_width) // 2
                        label_y = int(bottle_h * 0.26)  # 더 위로
                        
                        final_composite = bottle_img.copy()
                        final_composite.paste(label_resized, (label_x, label_y), label_resized)
                        
                        st.image(final_composite, caption="최종 제품 예상도", width=250)
                        
                    except FileNotFoundError:
                        st.warning("'bottle_mockup.png' 파일이 없습니다.")
                    
                    st.success("✅ 라벨이 성공적으로 생성되었습니다!")
                    
                except Exception as e:
                    st.error(f"오류 발생: {e}")

# --- 하단 네비게이션 버튼 ---
st.write("")
st.write("")

nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

with nav_col2:
    btn_cols = st.columns([1, 1])
    
    with btn_cols[0]:
        if st.session_state.step > 1:
            if st.button("이전", type="secondary", use_container_width=True):
                go_prev()
                st.rerun()
    
    with btn_cols[1]:
        if st.session_state.step < 4:
            if st.button("다음", type="primary", use_container_width=True):
                go_next()
                st.rerun()
