import os
import streamlit as st
import openai
import requests
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

# 페이지 설정
st.set_page_config(page_title="AI 패션 어드바이저", layout="wide")

# API 키 설정 (환경 변수에서 읽어오기)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY

# 제목과 설명
st.title("🎨 AI 날씨 기반 패션 어드바이저")
st.write("날씨와 개인 선호도에 맞는 패션을 추천해드립니다!")

# 사이드바 설정
with st.sidebar:
    st.header("설정")
    city = st.text_input("도시 이름 (영문)", value="Seoul")
    style_preferences = st.text_area(
        "스타일 선호도",
        placeholder="선호하는 스타일, 색상, 브랜드 등을 입력해주세요\n예: 캐주얼한 스타일, 블랙 계열, 미니멀한 디자인"
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

def get_fashion_recommendation(weather_data, style_preferences):
    """날씨와 스타일 선호도에 기반한 패션 추천을 생성합니다."""
    prompt = f"""날씨 조건:
    - 기온: {weather_data['temperature']}°C
    - 날씨 상태: {weather_data['description']}
    - 습도: {weather_data['humidity']}%
    
    스타일 선호도:
    {style_preferences}
    
    위 조건에 맞는 패션 코디를 추천해주세요. 구체적으로 설명해주세요."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 패션 전문가입니다. 날씨와 개인 선호도에 맞는 옷차림을 추천해주세요."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        st.error(f"패션 추천을 생성하는데 실패했습니다: {str(e)}")
        return None

def get_outfit_prompt(recommendation):
    """패션 추천을 간단한 영어 프롬프트로 변환합니다."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Convert the fashion recommendation into a short, clear English description for image generation. Keep it under 200 characters."},
                {"role": "user", "content": recommendation}
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        st.error(f"프롬프트 변환에 실패했습니다: {str(e)}")
        return None

def generate_image_with_dalle(recommendation):
    """DALL-E를 사용하여 추천된 패션의 이미지를 생성합니다."""
    try:
        # 긴 추천사항을 간단한 프롬프트로 변환
        outfit_prompt = get_outfit_prompt(recommendation)
        if not outfit_prompt:
            return None
            
        # 이미지 생성을 위한 최종 프롬프트 구성
        final_prompt = f"Fashion photo of a person wearing {outfit_prompt}, studio lighting, full body shot"
        
        # 프롬프트 길이 체크
        if len(final_prompt) > 1000:
            st.warning("프롬프트가 너무 깁니다. 더 간단한 설명으로 시도합니다.")
            final_prompt = f"Fashion photo of {outfit_prompt[:200]}, studio lighting"
        
        response = openai.Image.create(
            prompt=final_prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        
        # URL에서 이미지 다운로드
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            return Image.open(io.BytesIO(image_response.content))
        else:
            st.error("이미지 다운로드에 실패했습니다.")
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
                recommendation = get_fashion_recommendation(weather_data, style_preferences)
            
            if recommendation:
                st.subheader("🎯 패션 추천")
                st.write(recommendation)
                
                # 이미지 생성
                with st.spinner("패션 이미지를 생성하는 중..."):
                    image = generate_image_with_dalle(recommendation)
                    
                if image:
                    st.subheader("👗 스타일 시각화")
                    st.image(image, caption="AI가 생성한 패션 이미지", use_column_width=True)

# 추가 정보
st.markdown("---")
st.markdown("""
### 사용 방법
1. 사이드바에서 도시 이름을 영문으로 입력하세요 (예: Seoul, Busan, Tokyo)
2. 원하는 스타일, 선호하는 색상, 브랜드 등을 자세히 입력해주세요
3. '패션 추천 받기' 버튼을 클릭하세요

⚠️ 참고: OpenWeatherMap API와 OpenAI API 키가 필요합니다.
""")