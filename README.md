# AI 패션 추천 어드바이저 (with.weather)

## 소개

**AI 패션 추천 어드바이저**는 사용자의 위치(도시), 성별, 키, 몸무게, 스타일 선호도, 그리고 실시간 날씨 정보를 바탕으로  
최적의 패션 코디를 추천하고, AI 이미지 생성 모델을 통해 해당 스타일의 이미지를 시각화해주는 웹 애플리케이션입니다.

- 날씨 API, OpenAI GPT, Hugging Face Diffusers(Stable Diffusion) 등 다양한 AI/외부 API를 활용합니다.
- Streamlit 기반의 직관적인 UI를 제공합니다.

---

## 주요 기능

1. **날씨 정보 조회**  
   - OpenWeather API를 통해 입력한 도시의 실시간 날씨(기온, 상태, 습도)를 조회합니다.

2. **맞춤형 패션 추천**  
   - 사용자의 성별, 키, 몸무게, 스타일 선호도, 날씨 정보를 바탕으로 OpenAI GPT를 활용해 텍스트 패션 코디를 추천합니다.

3. **AI 패션 이미지 생성**  
   - 추천된 패션 코디를 바탕으로, Hugging Face의 Stable Diffusion API를 통해 해당 스타일의 이미지를 생성합니다.

4. **직관적인 웹 UI**  
   - Streamlit을 사용하여, 사이드바 입력 → 추천 결과 및 이미지 표시까지 한 번에 제공합니다.

---

## 사용 방법

1. **사이드바에서 정보 입력**
   - 도시 이름(영문), 성별, 키, 몸무게, 스타일 선호도를 입력합니다.
2. **'패션 추천 받기' 버튼 클릭**
3. **결과 확인**
   - 날씨 정보, 맞춤형 패션 추천, AI가 생성한 패션 이미지가 순서대로 표시됩니다.

---

## 전체 구조 다이어그램

```mermaid
flowchart TD
    A[사용자 입력 (도시, 성별, 키, 몸무게, 스타일)] --> B[날씨 정보 조회 (OpenWeather API)]
    B --> C[패션 추천 생성 (OpenAI GPT)]
    C --> D[패션 이미지 생성 (Hugging Face Stable Diffusion)]
    D --> E[결과 출력 (Streamlit UI)]
    C --> E
    B --> E
```

---

## 주요 코드 구조

- **app.py**
  - 환경 변수 로드 및 API 키 설정
  - Streamlit UI 구성 (사이드바 입력, 메인 결과 영역)
  - `get_weather`: 도시의 날씨 정보 조회
  - `get_fashion_recommendation`: GPT를 활용한 패션 추천 생성
  - `get_outfit_prompt`: 추천 결과를 이미지 생성용 프롬프트로 변환
  - `generate_image_with_huggingface`: Stable Diffusion API로 패션 이미지 생성
  - 메인 실행 로직: 입력값 검증 → 날씨 조회 → 패션 추천 → 이미지 생성 → 결과 표시

---

## 환경 변수(.env 예시)
