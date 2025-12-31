# Perfume Label Generator v0.6 (2025-12-31)
# - v2와 별개로, 간단하게 수정/실험 가능한 버전
# - 주요 기능: 기본 정보 입력, 아트스타일 선택, 참고사진 업로드(왼쪽정렬, 회색박스X)

import streamlit as st
from PIL import Image

st.set_page_config(page_title="라벨 생성기 v0.6", layout="centered")
st.title("향수 라벨 생성기 v0.6")

# 1. 기본 정보 입력
st.header("1. 기본 정보")
name = st.text_input("이름")
desc = st.text_area("설명")

# 2. 아트스타일 선택
st.header("2. 아트스타일")
art_styles = ["유화", "수채화", "네오익스프레셔니즘"]
art_style = st.radio("스타일을 선택하세요", art_styles, horizontal=True)

# 3. 참고사진 첨부 (왼쪽정렬, 회색박스X)
st.header("3. 참고사진 (선택)")
st.markdown("""
<style>
[data-testid="stFileUploader"] section {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stFileUploader"] section > div {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)
col_upload, _ = st.columns([1, 2])
with col_upload:
    ref_image = st.file_uploader("파일 열기", type=["png", "jpg", "jpeg"], key="ref_image_upload")
    if ref_image:
        img = Image.open(ref_image)
        st.image(img, width=120)

# 4. 생성 버튼
if st.button("라벨 생성하기"):
    st.success(f"{name}님의 라벨이 생성되었습니다! (스타일: {art_style})")
    if ref_image:
        st.image(img, width=200, caption="참고사진")
    st.write(f"설명: {desc}")

st.caption("v0.6 - 실험/수정용 단순 버전. v2와 별개로 동작합니다.")

st.markdown("""
<style>
@media (min-width: 700px) and (max-width: 1100px) {
  button[kind="secondary"] {
    min-width: 120px !important;
    padding-left: 24px !important;
    padding-right: 24px !important;
    font-size: 1.1em !important;
  }
}
</style>
""", unsafe_allow_html=True)
