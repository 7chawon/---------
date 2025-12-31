import streamlit as st
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# --- 설정 ---
api_key = "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"  # 실제 사용 시 환경변수 권장
client = OpenAI(api_key=api_key)

st.set_page_config(layout="wide", page_title="Perfume Studio Pro")

st.title("✨ Celebrity Perfume Studio: Step 3 (Logo Integration)")
st.markdown("브랜드 로고를 포함하여 실제 출시될 제품의 라벨을 완성합니다.")

# --- 화면 분할 ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. Design Elements")
    with st.form("design_form"):
        # A. 로고 및 텍스트 정보
        st.markdown("##### 🔹 브랜드 & 로고")
        # 파일 업로더 추가 (PNG만 허용)
        uploaded_logo = st.file_uploader("로고 이미지 파일 업로드 (배경 투명한 PNG 권장)", type=["png"])
        logo_size_percent = st.slider("로고 크기 비율 (%)", 10, 50, 30)
        
        st.markdown("##### 🔹 텍스트 정보")
        perfume_name = st.text_input("향수 이름", "Midnight Blue")
        celeb_name = st.text_input("셀럽 이름 / 문구", "Designed by V")
        text_color = st.color_picker("텍스트 색상", "#FFFFFF")

        st.divider()

        # B. 배경(Mood) 스토리텔링
        st.markdown("##### 🔹 배경 아트워크 (AI)")
        memory = st.text_area("담고 싶은 분위기/기억", "깊은 밤, 달빛이 비추는 조용한 바다와 은은한 우드 향")
        art_style = st.selectbox("아트 스타일", ["Oil Painting (유화)", "Watercolor (수채화)", "Abstract (추상화)", "Minimal Gradient (그라데이션)"])
        
        # C. 합성 옵션
        st.divider()
        overlay_opacity = st.slider("최종 라벨 투명도 (공병 질감 반영)", 50, 100, 95)
        
        submitted = st.form_submit_button("✨ 디자인 완성 및 시뮬레이션")

# --- 로직 처리 ---
if submitted:
    if not api_key:
        st.error("API 키를 입력해주세요.")
    else:
        with col2:
            status_box = st.status("작업 진행 중...", expanded=True)
            
            try:
                # --- [수정] DALL-E 대신 임시 배경 사용 (테스트 모드) ---
                # status_box.write("🎨 AI가 배경 아트워크를 그리고 있습니다...")
                # prompt = f"""
                # Artistic background pattern for a luxury perfume label.
                # Theme: {memory}.
                # Style: {art_style}. High quality, elegant textures.
                # Important: NO TEXT, NO LOGOS. Just background art. Aspect Ratio: Square.
                # """
                # response = client.images.generate(
                #     model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1
                # )
                # img_url = response.data[0].url
                # res = requests.get(img_url)
                # base_label_img = Image.open(BytesIO(res.content)).convert("RGBA")
                
                status_box.write("⚠️ 결제 한도 도달로 '테스트용 파란 배경'을 사용합니다.")
                # 1024x1024 크기의 단색 배경 생성
                base_label_img = Image.new('RGBA', (1024, 1024), color='#3d5afe')
                W, H = base_label_img.size
                # -------------------------------------------------------------

                # 2. [Layer 2 - 중간] 로고 합성 (업로드된 경우만)
                if uploaded_logo is not None:
                    status_box.write("이미지 레이어 합성 중: 로고 배치...")
                    logo_img = Image.open(uploaded_logo).convert("RGBA")
                    
                    # 로고 크기 조절 (라벨 너비의 N%로 설정)
                    target_logo_w = int(W * (logo_size_percent / 100))
                    w_percent = (target_logo_w / float(logo_img.size[0]))
                    h_size = int((float(logo_img.size[1]) * float(w_percent)))
                    logo_resized = logo_img.resize((target_logo_w, h_size), Image.Resampling.LANCZOS)
                    
                    # 로고 위치 계산 (상단 중앙 정렬, 위에서 약간 띄움)
                    logo_x = (W - target_logo_w) // 2
                    logo_y = int(H * 0.1)  # 상단에서 10% 지점

                    # 로고 붙이기 (mask=logo_resized를 써야 투명 배경이 유지됨 중요!)
                    base_label_img.paste(logo_resized, (logo_x, logo_y), logo_resized)
                    text_start_y = logo_y + h_size + 50  # 텍스트 시작 위치를 로고 아래로 조정
                else:
                    text_start_y = H // 2 - 50  # 로고 없으면 중앙 부근

                # 3. [Layer 3 - 상단] 텍스트 합성
                status_box.write("이미지 레이어 합성 중: 텍스트 각인...")
                draw = ImageDraw.Draw(base_label_img)
                try:
                    title_font = ImageFont.truetype("font.ttf", 110)
                    sub_font = ImageFont.truetype("font.ttf", 50)
                except:
                    title_font = ImageFont.load_default()
                    sub_font = ImageFont.load_default()

                # 텍스트 그리기 (anchor="mt": 상단 중앙 기준점)
                draw.text((W / 2, text_start_y), perfume_name, font=title_font, fill=text_color, anchor="mt")
                draw.text((W / 2, text_start_y + 140), celeb_name, font=sub_font, fill=text_color, anchor="mt")
                
                # 완성된 라벨 표시
                st.image(base_label_img, caption="완성된 라벨 디자인 (배경+로고+텍스트)", width=400)
                
                # 4. 최종 목업(Mockup) 합성
                status_box.write("🧴 최종 제품 시뮬레이션 중...")
                try:
                    bottle_img = Image.open("bottle_mockup.png").convert("RGBA")
                    bottle_w, bottle_h = bottle_img.size
                    
                    # --- 합성 좌표 (공병 크기에 맞춰 자동 조정) ---
                    # 라벨 너비를 공병 너비의 100%로 설정
                    target_width = int(bottle_w * 1.0)
                    target_height = 400  # 세로 길이 직접 px 설정
                    label_resized = base_label_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    
                    # 투명도 적용
                    alpha = int(255 * (overlay_opacity / 100))
                    label_resized.putalpha(alpha)

                    # 병에 부착 (중앙 정렬, 유리 본체 중앙 위치)
                    label_x = (bottle_w - target_width) // 2
                    label_y = int(bottle_h * 0.35)  # 상단에서 35% 지점 (뚜껑 아래 유리 중앙)
                    
                    final_composite = bottle_img.copy()
                    final_composite.paste(label_resized, (label_x, label_y), label_resized)
                    
                    st.image(final_composite, caption="최종 제품 예상도", width=250)
                    status_box.update(label="작업 완료!", state="complete", expanded=False)
                    
                except FileNotFoundError:
                    st.warning("'bottle_mockup.png' 공병 이미지가 없습니다.")
                    status_box.update(label="라벨 생성 완료 (공병 없음)", state="complete")

            except Exception as e:
                st.error(f"에러 발생: {e}")
                status_box.update(label="에러 발생", state="error")
