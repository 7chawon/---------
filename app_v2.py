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
        
        # 로딩 중 표시 (2개)
        cols = st.columns(2)
        for i in range(2):
            with cols[i]:
                st.markdown(f"""
                <div style="width: 100%; aspect-ratio: 1; background: #1a1a1a; border-radius: 8px;
                     border: 1px solid #333; display: flex; align-items: center; justify-content: center;">
                    <div>
                        <span class="loading-dot"></span>
                        <span class="loading-dot"></span>
                        <span class="loading-dot"></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # API 호출해서 이미지 생성
        with st.spinner("AI가 이미지를 생성 중입니다..."):
            try:
                prompt = st.session_state.form_data.get('ai_prompt', '우아한 라벨 디자인')
                art_style = st.session_state.form_data.get('art_style', '단색 배경')
                reference_style = st.session_state.get('reference_style_desc', '')
                
                # 아트 스타일 영문 변환
                style_map = {
                    "단색 배경": "clean solid color background, minimalist luxury",
                    "Oil Painting (유화)": "masterful oil painting style by a skilled human artist, visible brushwork, rich impasto textures, classical European master painting quality",
                    "Watercolor (수채화)": "delicate hand-painted watercolor by professional illustrator, soft ethereal washes, subtle color bleeding, traditional media feel",
                    "Abstract (추상화)": "neo-expressionist hand-painted art, bold expressive human brushstrokes, gallery-worthy contemporary fine art",
                    "Minimal Gradient (그라데이션)": "sophisticated hand-crafted gradient, smooth luxurious color transitions, artisanal quality"
                }
                style_desc = style_map.get(art_style, "minimalist, elegant, hand-crafted quality")
                
                # 레퍼런스 이미지 스타일 추가
                reference_part = ""
                if reference_style:
                    reference_part = f"\n                Reference Style Guide: {reference_style}"
                
                full_prompt = f"""
                Create a pure fine art painting. This is NOT for any product or packaging.
                
                Subject & Theme: {prompt}
                
                CRITICAL Art Direction:
                - Style: {style_desc}
                - This is a standalone artwork for a gallery exhibition
                - MUST look like genuine hand-painted traditional art by a master artist
                - Quality: Museum-worthy, professional artist level, sophisticated
                - Visible artistic techniques: brushstrokes, texture, artistic imperfections that show human touch
                - Mood: Evocative, atmospheric, emotionally resonant
                - Composition: Balanced, intentional negative space, elegant framing
                - Color palette: Harmonious, tasteful, refined color choices
                - Lighting: Painterly, dimensional, creates depth
                {reference_part}
                
                ABSOLUTELY FORBIDDEN - DO NOT INCLUDE ANY OF THESE:
                - Bottles of any kind (perfume bottles, glass bottles, wine bottles, any container)
                - Vials, jars, flasks, or any glass containers
                - Product packaging, boxes, or commercial elements
                - Sprayers, atomizers, or dispensers
                - Text, typography, letters, logos, brand names, or words
                - Labels or tags
                - Digital-looking or CGI effects
                - Cartoonish or childish elements
                
                This artwork should contain ONLY: {prompt}
                Nothing else. No objects that weren't specifically requested.
                
                Technical requirements:
                - Square format (1:1 aspect ratio)
                - Pure artistic illustration with ONLY the requested subject
                - Timeless fine art quality
                - Inspired by classical and contemporary fine artists
                """
                
                # DALL-E API 호출 (2개 이미지)
                generated_images = []
                for i in range(2):
                    try:
                        response = client.images.generate(
                            model="dall-e-3",
                            prompt=full_prompt,
                            size="1024x1024",
                            quality="standard",
                            n=1,
                        )
                        img_url = response.data[0].url
                        res = requests.get(img_url)
                        img = Image.open(BytesIO(res.content))
                        generated_images.append(img)
                    except Exception as e:
                        # API 실패 시 테스트용 이미지 생성
                        test_colors = ['#3d5afe', '#e91e63']
                        test_img = Image.new('RGBA', (256, 256), color=test_colors[i])
                        generated_images.append(test_img)
                
                st.session_state.ai_generated_images = generated_images
                st.session_state.ai_generating = False
                st.rerun()
                
            except Exception as e:
                st.error(f"이미지 생성 중 오류: {e}")
                st.session_state.ai_generating = False
    else:
        # 생성된 이미지 표시 (2개)
        cols = st.columns(2)
        for i, img in enumerate(st.session_state.ai_generated_images):
            with cols[i]:
                st.image(img, use_container_width=True)
                if st.button("➕", key=f"select_ai_img_{i}", use_container_width=True):
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
    # 채팅 히스토리 초기화
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "안녕하세요! 라벨에 어떤 주제를 담고 싶으신가요? 🎨\n\n아래에서 선택하거나 직접 입력해주세요!"}
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
        "Abstract (추상화)": "style_abstract.png"
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
        is_positive_response = any(kw in user_lower for kw in positive_keywords)
        is_direct_request = any(kw in user_lower for kw in ["생성해", "만들어", "생성 해", "만들어 줘"])
        
        # 긍정 답변이거나 직접 생성 요청인 경우 바로 이미지 생성
        if (is_asking_generate and is_positive_response) or is_direct_request:
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
                    
                    # 사물은 바로 대화 입력으로
                    if value == "사물":
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 💎 어떤 사물을 원하시나요? 자유롭게 설명해주세요!"})
                        st.session_state.chat_step = 5  # 날씨 단계로
                    else:
                        responses = {
                            "사람": "멋져요! 👤 성별을 선택해주세요.",
                            "동물": "귀여워요! 🐾 성별을 선택해주세요.",
                            "식물": "자연스럽네요! 🌸 어떤 종류의 식물인가요?"
                        }
                        st.session_state.chat_messages.append({"role": "assistant", "content": responses[value]})
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
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 나이대를 선택해주세요."})
                        st.session_state.chat_step = 3
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
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 나이대를 선택해주세요."})
                        st.session_state.chat_step = 3
                        st.rerun()
                        
        elif subject == "식물":
            st.markdown("**🌸 식물 종류** (클릭하면 자동 입력)")
            plant_opts = [("🌸 꽃", "꽃"), ("🌳 나무", "나무")]
            kw_cols = st.columns(2)
            for i, (label, value) in enumerate(plant_opts):
                with kw_cols[i]:
                    if st.button(label, key=f"plant_{i}", use_container_width=True):
                        st.session_state.ai_selections['plant_type'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🌿 식물의 양은 어느 정도로 할까요?"})
                        st.session_state.chat_step = 4
                        st.rerun()
    
    # 3단계: 나이대 선택 (사람/동물)
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
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🌤️ 이제 날씨를 선택해주세요."})
                        st.session_state.chat_step = 5
                        st.rerun()
                        
        elif subject == "동물":
            st.markdown("**🐾 나이대 선택** (클릭하면 자동 입력)")
            age_opts = [("🐣 아기", "아기"), ("🐕 청년", "청년"), ("🐕‍🦺 성체", "성체"), ("🐶 노년", "노년")]
            kw_cols = st.columns(4)
            for i, (label, value) in enumerate(age_opts):
                with kw_cols[i]:
                    if st.button(label, key=f"animal_age_{i}", use_container_width=True):
                        st.session_state.ai_selections['age'] = value
                        st.session_state.chat_messages.append({"role": "user", "content": value})
                        st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🌤️ 이제 날씨를 선택해주세요."})
                        st.session_state.chat_step = 5
                        st.rerun()
    
    # 4단계: 식물의 양 선택
    elif current_step == 4:
        st.markdown("**🌿 식물의 양** (클릭하면 자동 입력)")
        amount_opts = [("🌱 조금", "조금만"), ("🌿 적당히", "적당히"), ("🌳 많이", "많이"), ("🌲 가득", "가득 채워서")]
        kw_cols = st.columns(4)
        for i, (label, value) in enumerate(amount_opts):
            with kw_cols[i]:
                if st.button(label, key=f"amount_{i}", use_container_width=True):
                    st.session_state.ai_selections['amount'] = value
                    st.session_state.chat_messages.append({"role": "user", "content": value})
                    st.session_state.chat_messages.append({"role": "assistant", "content": "좋아요! 🌤️ 이제 날씨를 선택해주세요."})
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
                    st.session_state.chat_messages.append({"role": "user", "content": f"{value} 분위기로 해주세요"})
                    st.session_state.chat_messages.append({"role": "assistant", "content": f"완벽해요! ✨ 모든 선택이 완료되었습니다.\n\n👉 '이미지 생성' 버튼을 눌러주세요!"})
                    st.session_state.chat_step = 10
                    st.rerun()
        
        for i, (label, value) in enumerate(mood_opts[3:]):
            with row2[i]:
                if st.button(label, key=f"mood_{i+3}", use_container_width=True):
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
    col_back, col_title = st.columns([0.3, 1])
    with col_back:
        if st.button("←", key="back_btn", help="처음으로"):
            reset_form()
    with col_title:
        st.markdown("**라벨 만들기**")

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
            ("신표현주의", "Abstract (추상화)", "style_abstract.png")
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
        
        # 2행: 유화, 수채화, 신표현주의 (3열) - 썸네일 미리보기 포함
        row2_cols = st.columns(3)
        for i in range(2, 5):
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
        
        art_style = st.session_state.form_data.get('art_style', None)
        
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
                    
                    # 배경 이미지 생성
                    no_bg = data.get('no_bg', False)
                    if no_bg:
                        # 투명 배경
                        base_label_img = Image.new('RGBA', (1024, 1024), color=(0, 0, 0, 0))
                    else:
                        bg_color = data.get('bg_color', '#3d5afe')
                        base_label_img = Image.new('RGBA', (1024, 1024), color=bg_color)
                    W, H = base_label_img.size
                    
                    # 선택된 라벨 이미지 합성 (상단)
                    label_images = data.get('label_images', [])
                    selected_idx = data.get('selected_image_idx')
                    
                    if label_images and selected_idx is not None and selected_idx < len(label_images):
                        selected_img = label_images[selected_idx]
                        # PIL Image인지 UploadedFile인지 확인
                        if hasattr(selected_img, 'read'):
                            # UploadedFile
                            label_art = Image.open(selected_img).convert("RGBA")
                        else:
                            # PIL Image
                            label_art = selected_img.convert("RGBA")
                        
                        # 이미지를 라벨 전체 크기로 맞춤 (cover 방식 - 비율 유지하면서 꽉 채움)
                        img_w, img_h = label_art.size
                        target_w, target_h = W, H
                        
                        # 비율 계산 (cover: 더 큰 비율 사용)
                        scale = max(target_w / img_w, target_h / img_h)
                        new_w = int(img_w * scale)
                        new_h = int(img_h * scale)
                        
                        # 리사이즈
                        art_resized = label_art.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        
                        # 중앙 크롭
                        left = (new_w - target_w) // 2
                        top = (new_h - target_h) // 2
                        art_cropped = art_resized.crop((left, top, left + target_w, top + target_h))
                        
                        # 전체 배경으로 사용 (0, 0 위치에)
                        base_label_img.paste(art_cropped, (0, 0), art_cropped)
                        text_start_y = int(H * 0.75)  # 텍스트는 하단에
                    else:
                        text_start_y = int(H * 0.3)
                    
                    # 회사 로고 합성 (하단 고정, 20% 크기)
                    try:
                        company_logo = Image.open("logo.png").convert("RGBA")
                        logo_size_percent = 20  # 20% 고정
                        target_logo_w = int(W * (logo_size_percent / 100))
                        w_percent = (target_logo_w / float(company_logo.size[0]))
                        h_size = int((float(company_logo.size[1]) * float(w_percent)))
                        logo_resized = company_logo.resize((target_logo_w, h_size), Image.Resampling.LANCZOS)
                        logo_x = (W - target_logo_w) // 2
                        logo_y = int(H * 0.85) - h_size  # 하단에서 15% 위치
                        base_label_img.paste(logo_resized, (logo_x, logo_y), logo_resized)
                    except FileNotFoundError:
                        pass  # logo.png 없으면 스킵
                    
                    # 텍스트 합성
                    draw = ImageDraw.Draw(base_label_img)
                    try:
                        title_font = ImageFont.truetype("font.ttf", 110)
                        sub_font = ImageFont.truetype("font.ttf", 50)
                    except:
                        title_font = ImageFont.load_default()
                        sub_font = ImageFont.load_default()
                    
                    text_color = data.get('text_color', '#FFFFFF')
                    perfume_name = data.get('perfume_name', 'Perfume Name')
                    celeb_name = data.get('celeb_name', '')
                    
                    draw.text((W / 2, text_start_y), perfume_name, font=title_font, fill=text_color, anchor="mt")
                    if celeb_name:
                        draw.text((W / 2, text_start_y + 140), celeb_name, font=sub_font, fill=text_color, anchor="mt")
                    
                    # 라벨 표시
                    st.image(base_label_img, caption="생성된 라벨", width=300)
                    
                    # 공병 합성
                    st.markdown("---")
                    st.markdown("#### 🧴 제품 목업")
                    
                    try:
                        bottle_img = Image.open("bottle_mockup.png").convert("RGBA")
                        bottle_w, bottle_h = bottle_img.size
                        
                        target_width = int(bottle_w * 1.0)
                        target_height = 400
                        label_resized = base_label_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                        
                        alpha = int(255 * (data.get('label_opacity', 95) / 100))
                        label_resized.putalpha(alpha)
                        
                        label_x = (bottle_w - target_width) // 2
                        label_y = int(bottle_h * 0.35)
                        
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
