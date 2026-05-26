import streamlit as st
import pandas as pd
import requests

# 1. 페이지 기본 설정
st.set_page_config(page_title="Weather Playlist", page_icon="🎧", layout="wide")

# 2. 스포티파이 다크 테마 커스텀 디자인
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
    .play-btn {
        background-color: #1DB954;
        color: black !important;
        padding: 12px 30px;
        border-radius: 30px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        font-size: 14px;
        box-shadow: 0 4px 15px rgba(29, 185, 84, 0.3);
    }
    .play-btn:hover {
        background-color: #1ed760;
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 및 전처리
@st.cache_data
def load_data():
    df = pd.read_csv('spotify-2023.csv', encoding='latin-1')
    df.columns = [c.strip() for c in df.columns]
    df['streams'] = pd.to_numeric(df['streams'], errors='coerce')
    return df

df = load_data()

# 4. 사이드바 제어 패널 구성
st.sidebar.title("📍 Weather Playlist 제어판")

# [기능 1] 실시간 위치 및 날씨 데이터 동기화
with st.sidebar.expander("🔍 실시간 날씨 데이터 불러오기", expanded=True):
    city_input = st.text_input("영문 도시명 입력 (예: Daejeon)", placeholder="Seoul")
    if st.button("날씨 데이터 동기화"):
        if city_input:
            api_key = "5c55a17e72f6d32c9e75968bdd7beb19" # 본인의 API 키
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={city_input}&appid={api_key}&units=metric"
            try:
                res = requests.get(w_url).json()
                if res.get("cod") == 200:
                    st.session_state['temp'] = float(res['main']['temp'])
                    st.session_state['hum'] = float(res['main']['humidity'])
                    st.success(f"{city_input} 데이터 연동 완료!")
                else: st.error("도시를 찾을 수 없습니다.")
            except: st.error("API 연결 실패")

# 세션 상태 초기화 (슬라이더 동기화용)
if 'temp' not in st.session_state: st.session_state['temp'] = 22.0
if 'hum' not in st.session_state: st.session_state['hum'] = 50.0

# [기능 2] 사계절 및 정밀 수치 시뮬레이터 (v3.5 + v4.5)
season = st.sidebar.selectbox("분석 계절 설정", ["봄 (3-5월)", "여름 (6-8월)", "가을 (9-11월)", "겨울 (12-2월)", "전체 시즌"])
temp = st.sidebar.slider("정밀 온도 조절 (℃)", -20.0, 40.0, st.session_state['temp'], 0.1)
hum = st.sidebar.slider("정밀 습도 조절 (%)", 0.0, 100.0, st.session_state['hum'], 0.1)
vibe = st.sidebar.slider("현재 나의 기분 (0:차분함 ↔ 100:신남)", 0.0, 100.0, 50.0, 0.1)

# 5. 메인 화면 출력
st.title("🎧 Weather Playlist v5.5")
st.write("실시간 기상 데이터와 사계절 스트리밍 빅데이터를 분석하여 당신의 감성에 가장 최적화된 곡들을 제안합니다.")

# [기능 3] 지능형 새로고침 버튼 (v5.5)
if st.button("🚀 나만의 플레이리스트 생성 및 새로고침"):
    # 가중치 알고리즘 (날씨 60% + 사용자 기분 40%)
    t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
    t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
    
    # 사계절 데이터 필터링
    if "봄" in season: candidates = df[df['released_month'].isin([3, 4, 5])]
    elif "여름" in season: candidates = df[df['released_month'].isin([6, 7, 8])]
    elif "가을" in season: candidates = df[df['released_month'].isin([9, 10, 11])]
    elif "겨울" in season: candidates = df[df['released_month'].isin([12, 1, 2])]
    else: candidates = df
    
    candidates = candidates.copy()
    # 수치 유사도 분석 (오차 점수 계산)
    candidates['score'] = (candidates['energy_%'] - t_e).abs() + (candidates['valence_%'] - t_v).abs()
    
    # [지능형 새로고침]: 상위 100곡 중 30곡 무작위 추출
    results = candidates.sort_values(by='score').head(100).sample(30)
    
    st.info(f"✅ 분석 완료! {season} 테마 | 기온 {temp}℃, 습도 {hum}% 에 최적화된 30곡의 리스트입니다.")

    # 6. 결과 출력 (카드형 UI + 다이렉트 플레이어)
    for i, (idx, row) in enumerate(results.iterrows()):
        track, artist = row['track_name'], row['artist(s)_name']
        # [기능 4] 스포티파이 앱/웹 즉시 연동 링크
        play_url = f"https://open.spotify.com/search/{track} {artist}"
        
        st.markdown(f"""
            <div class="song-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #b3b3b3; font-size: 13px;">AI RECOMMENDATION</span><br>
                        <b style="font-size: 24px;">{track}</b><br>
                        <span style="color: #1DB954; font-size: 18px; font-weight: bold;">{artist}</span>
                    </div>
                    <div style="text-align: right;">
                        <p style="color: #b3b3b3; font-size: 12px; margin-bottom: 8px;">Energy: {row['energy_%']}% | Valence: {row['valence_%']}%</p>
                        <a href="{play_url}" target="_blank" class="play-btn">▶ PLAY NOW</a>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)