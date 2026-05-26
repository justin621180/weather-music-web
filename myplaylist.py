import streamlit as st
import pandas as pd
import requests
import unicodedata # 성조 및 특수 문자 정규화를 위한 라이브러리
from functools import partial

# 1. 페이지 기본 설정
st.set_page_config(page_title="Weather Playlist", page_icon="🎧", layout="wide")

# 2. 디자인 테마 (Spotify & Dark UI)
st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    .stSlider { color: #1DB954; }
    .song-card { 
        background-color: #181818; 
        padding: 25px; 
        border-radius: 15px; 
        border-left: 6px solid #1DB954; 
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        transition: 0.3s;
    }
    .song-card:hover {
        background-color: #282828;
        transform: translateY(-5px);
    }
    .btn-container { display: flex; gap: 10px; margin-top: 15px; }
    .play-btn {
        background-color: #1DB954;
        color: black !important;
        padding: 10px 20px;
        border-radius: 25px;
        text-decoration: none;
        font-weight: bold;
        font-size: 13px;
        flex: 1; text-align: center;
    }
    .yt-btn {
        background-color: #FF0000;
        color: white !important;
        padding: 10px 20px;
        border-radius: 25px;
        text-decoration: none;
        font-weight: bold;
        font-size: 13px;
        flex: 1; text-align: center;
    }
    .play-btn:hover { background-color: #1ed760; }
    .yt-btn:hover { background-color: #cc0000; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 및 [알파벳 정규화 전처리]
@st.cache_data
def load_data():
    try:
        # 데이터 로드
        df = pd.read_csv('spotify-2023.csv', encoding='latin-1')
        
        # [핵심 로직]: 모든 성조(é, ñ, á 등)를 표준 알파벳(e, n, a)으로 변환하는 함수
        def normalize_text(text):
            if not isinstance(text, str): return text
            # 유니코드 NFD 정규화: 'é'를 'e'와 '성조표시'로 분리
            text = unicodedata.normalize('NFD', text)
            # 성조 표시(combining marks)만 제외하고 다시 합침
            clean_text = "".join([c for c in text if not unicodedata.combining(c)])
            # ASCII 영역을 벗어나는 깨진 특수기호 강제 제거
            return clean_text.encode('ascii', 'ignore').decode('ascii')

        # 곡명과 아티스트명에 정규화 적용
        df['track_name'] = df['track_name'].apply(normalize_text)
        df['artist(s)_name'] = df['artist(s)_name'].apply(normalize_text)
        
        df.columns = [c.strip() for c in df.columns]
        df['streams'] = pd.to_numeric(df['streams'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"데이터 정제 중 오류 발생: {e}")
        return None

df = load_data()

# 4. 사이드바 제어 패널 구성
st.sidebar.title("📍 Weather Playlist Control")

# [기능] 실시간 날씨 데이터 연동
with st.sidebar.expander("🔍 실시간 날씨 데이터 불러오기", expanded=True):
    city_input = st.text_input("영문 도시명 (예: Seoul)", placeholder="Seoul")
    if st.button("날씨 동기화"):
        if city_input:
            api_key = "5c55a17e72f6d32c9e75968bdd7beb19" # API 키
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={city_input}&appid={api_key}&units=metric"
            try:
                res = requests.get(w_url).json()
                if res.get("cod") == 200:
                    st.session_state['temp'] = float(res['main']['temp'])
                    st.session_state['hum'] = float(res['main']['humidity'])
                    st.success(f"{city_input} 데이터 동기화 완료!")
                else: st.error("도시를 찾을 수 없습니다.")
            except: st.error("API 연결 실패")

# 세션 초기값
if 'temp' not in st.session_state: st.session_state['temp'] = 22.0
if 'hum' not in st.session_state: st.session_state['hum'] = 50.0

# 정밀 시뮬레이터 슬라이더
season = st.sidebar.selectbox("분석 계절 설정", ["봄 (3-5월)", "여름 (6-8월)", "가을 (9-11월)", "겨울 (12-2월)", "전체 시즌"])
temp = st.sidebar.slider("온도 조절 (℃)", -20.0, 40.0, st.session_state['temp'], 0.1)
hum = st.sidebar.slider("습도 조절 (%)", 0.0, 100.0, st.session_state['hum'], 0.1)
vibe = st.sidebar.slider("사용자 기분 (0:차분함 ↔ 100:신남)", 0.0, 100.0, 50.0, 0.1)

# 5. 메인 화면 출력
st.title("🎧 Weather Playlist v7.3")
st.write("알파벳 정규화 처리 및 실시간 기상 분석을 통해 전 세계 노래 중 당신의 환경에 가장 정합한 30곡을 큐레이션합니다.")

# [핵심]: 분석 및 새로고침 실행
if st.button("🚀 나만의 플레이리스트 생성 및 새로고침"):
    # 가중치 알고리즘 산출 (날씨 60% + 사용자 40%)
    t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
    t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
    
    # 계절 필터링
    if "봄" in season: candidates = df[df['released_month'].isin([3, 4, 5])]
    elif "여름" in season: candidates = df[df['released_month'].isin([6, 7, 8])]
    elif "가을" in season: candidates = df[df['released_month'].isin([9, 10, 11])]
    elif "겨울" in season: candidates = df[df['released_month'].isin([12, 1, 2])]
    else: candidates = df
    
    candidates = candidates.copy()
    # 수치 유사도 점수 계산
    candidates['score'] = (candidates['energy_%'] - t_e).abs() + (candidates['valence_%'] - t_v).abs()
    
    # 상위 100곡 중 30곡 랜덤 샘플링 (지능형 새로고침)
    results = candidates.sort_values(by='score').head(100).sample(30)
    
    st.info(f"✅ 분석 완료: 온도 {temp}℃, 습도 {hum}% 최적화 결과 (목표 에너지: {t_e:.1f}%)")

    # 결과 카드 출력
    for i, (idx, row) in enumerate(results.iterrows()):
        track, artist = row['track_name'], row['artist(s)_name']
        play_url = f"https://open.spotify.com/search/{track} {artist}"
        yt_query = f"{track} {artist} official audio".replace(" ", "+")
        yt_url = f"https://www.youtube.com/results?search_query={yt_query}"
        
        mood_text = "밝고 경쾌한" if row['valence_%'] > 60 else "차분하고 서정적인"
        
        st.markdown(f"""
            <div class="song-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <b style="font-size: 24px; color: white;">{track}</b><br>
                        <span style="color: #1DB954; font-size: 18px; font-weight: bold;">{artist}</span>
                        <p style="color: #A1EAFB; font-size: 14px; margin-top: 10px;">
                            💬 {mood_text} 분위기 (에너지 {row['energy_%']}% / 밝기 {row['valence_%']}%)
                        </p>
                    </div>
                    <div style="width: 280px; text-align: right;">
                        <div class="btn-container">
                            <a href="{play_url}" target="_blank" class="play-btn">▶ Spotify</a>
                            <a href="{yt_url}" target="_blank" class="yt-btn">📺 YouTube</a>
                        </div>
                        <p style="color: #b3b3b3; font-size: 11px; margin-top: 15px;">
                            BPM: {row['bpm']} | Season: {row['released_month']}월
                        </p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)