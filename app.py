import os
import streamlit as st
import requests
from PIL import Image
import io
from dotenv import load_dotenv
from diffusers import StableDiffusionPipeline
import torch
import openai

# env파일 로드드
load_dotenv()

# 페이지 설정
st.set_page_config(page_title="AI 패션 추천 어드바이저", layout="wide")

# API 키 설정 (이전과 동일)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
openai.api_key = OPENAI_API_KEY

st.title("패션 추천 ai(with.weather)")

# 사이드바 설정
with st.sidebar:
    st.header("설정")
    city = st.text_input("도시 이름 (영문)", value="Seoul")

    gender = st.radio("성별", ["남성", "여성"], index=0)
    
    # 키와 몸무게 입력 추가
    height = st.number_input("키 (cm)", min_value=140, max_value=220, value=170)
    weight = st.number_input("몸무게 (kg)", min_value=30, max_value=150, value=60)
    
    style_preferences = st.text_area(
        "스타일 선호도",
        placeholder="선호하는 스타일, 색상등을 입력해주세요\n예: 캐주얼한 스타일, 블랙 계열, 미니멀한 디자인"
    )
    
    if st.button("패션 추천 받기", type="primary"):
        st.session_state.generate = True
    else:
        st.session_state.generate = False

def get_weather(city):
    """도시의 현재 날씨 정보를 가져옵니다."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            return {
                'temperature': data['main']['temp'],
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity']
            }
        else:
            st.error(f"날씨 정보를 가져오는데 실패했습니다: {data.get('message')}")
            return None
    except Exception as e:
        st.error(f"에러가 발생했습니다: {str(e)}")
        return None

def get_fashion_recommendation(weather_data, style_preferences, gender, height, weight):
    """날씨와 스타일 선호도, 체형에 기반한 패션 추천을 생성합니다."""
    # BMI 계산
    bmi = weight / ((height/100) ** 2)
    body_type = "마른" if bmi < 18.5 else "보통" if bmi < 25 else "통통한"
    
    # 성별에 따른 체형 특성 추가
    gender_specific = ""
    if gender == "남성":
        gender_specific = f"""
        남성복 특성:
        - 어깨와 가슴 부분의 실루엣을 고려한 핏
        - 남성적인 이미지를 살린 컬러와 디자인
        - 체형에 맞는 적절한 길이감"""
    else:
        gender_specific = f"""
        여성복 특성:
        - 허리와 힙 라인을 고려한 실루엣
        - 여성스러운 디테일과 악세서리 활용
        - 체형을 보완할 수 있는 스타일링"""

    prompt = f"""날씨 조건:
    - 기온: {weather_data['temperature']}°C
    - 날씨 상태: {weather_data['description']}
    - 습도: {weather_data['humidity']}%
    
    개인정보:
    - 성별: {gender}
    - 키: {height}cm
    - 몸무게: {weight}kg
    - 체형: {body_type} 체형
    
    {gender_specific}
    
    스타일 선호도:
    {style_preferences}
    
    위 조건들을 모두 고려하여:
    1. 체형에 어울리는 실루엣
    2. 날씨에 적합한 레이어링
    3. 성별에 맞는 스타일링
    4. 선호도를 반영한 컬러와 디자인
    
    이 모든 요소를 반영한 구체적인 패션 코디를 추천해주세요."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 패션 전문가입니다. 성별, 체형, 날씨를 종합적으로 고려하여 맞춤형 패션을 추천해주세요."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        st.error(f"패션 추천을 생성하는데 실패했습니다: {str(e)}")
        return None

def get_outfit_prompt(recommendation, gender, height, weight):
    """패션 추천을 이미지 생성용 프롬프트로 변환합니다."""
    gender_term = "male" if gender == "남성" else "female"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Convert the fashion recommendation into a clear, detailed prompt for generating a {gender_term} fashion image."},
                {"role": "user", "content": f"Gender: {gender_term}, Height: {height}cm, Weight: {weight}kg\n{recommendation}"}
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        st.error(f"프롬프트 변환에 실패했습니다: {str(e)}")
        return None

def generate_image_with_huggingface(gender, recommendation, height, weight):
    """Hugging Face의 Stable Diffusion API를 사용하여 패션 이미지를 생성합니다."""
    try:
        outfit_prompt = get_outfit_prompt(recommendation, gender, height, weight)
        if not outfit_prompt:
            return None
            
        # 성별과 체형 정보를 포함한 프롬프트 생성
        bmi = weight / ((height/100) ** 2)
        body_type = "slim" if bmi < 18.5 else "average" if bmi < 25 else "plus size"
        gender_term = "male" if gender == "남성" else "female"
        
        final_prompt = f"""full body fashion photo of a {gender_term} {body_type} person wearing {outfit_prompt}, 
        height {height}cm, {gender_term} body type, standing pose, full body from head to toe, 
        professional studio lighting, plain white background, centered composition, 
        fashion photography style, high quality, sharp focus, full shot, wide angle lens, 
        {gender_term} fashion model, {gender_term} appropriate styling"""
        
        negative_prompt = f"""cropped, zoomed in, close up, portrait, half body, 
        bad anatomy, bad proportions, blurry, deformed, disfigured, 
        duplicate, error, extra limbs, extra fingers, poorly drawn face, 
        poorly drawn hands, missing feet, missing legs, missing arms, 
        opposite gender characteristics, gender confusion, 
        inappropriate clothing for {gender_term}"""
        
        API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        
        response = requests.post(
            API_URL,
            headers=headers,
            json={
                "inputs": final_prompt,
                "parameters": {
                    "negative_prompt": negative_prompt,
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5,
                    "width": 384,
                    "height": 576
                }
            }
        )
        
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            return image.resize((384, 576), Image.Resampling.LANCZOS)
        else:
            st.error("이미지 생성에 실패했습니다.")
            return None
            
    except Exception as e:
        st.error(f"이미지 생성에 실패했습니다: {str(e)}")
        return None

# 메인 로직
if st.session_state.get('generate', False):
    if not city or not style_preferences:
        st.warning("도시 이름과 스타일 선호도를 모두 입력해주세요.")
    else:
        with st.spinner("날씨 정보를 가져오는 중..."):
            weather_data = get_weather(city)
            
        if weather_data:
            # 날씨 정보 표시
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("기온", f"{weather_data['temperature']}°C")
            with col2:
                st.metric("날씨", weather_data['description'])
            with col3:
                st.metric("습도", f"{weather_data['humidity']}%")
            
            # 패션 추천 생성
            with st.spinner("패션 추천을 생성하는 중..."):
                recommendation = get_fashion_recommendation(weather_data, style_preferences, gender, height, weight)
            
            if recommendation:
                st.subheader("🎯 패션 추천")
                st.write(recommendation)
                
                # 이미지 생성
                with st.spinner("패션 이미지를 생성하는 중..."):
                    image = generate_image_with_huggingface(gender, recommendation, height, weight)
                    
                if image:
                    st.subheader("👗 스타일 시각화")
                    st.image(image, caption="AI가 생성한 패션 이미지", width=384)

# 추가 정보
st.markdown("---")
st.markdown("""
### 사용 방법
1. 사이드바에서 도시 이름을 영문으로 입력하세요 (예: Seoul, Busan, Tokyo)
2. 성별을 선택하세요
3. 키와 몸무게를 입력해주세요
4. 원하는 스타일, 선호하는 색상, 브랜드 등을 자세히 입력해주세요
5. '패션 추천 받기' 버튼을 클릭하세요

⚠️ 참고: Hugging Face API는 하루 약 30,000개의 무료 요청이 가능하며, 비교적 빠른 응답 시간을 제공합니다.
""")