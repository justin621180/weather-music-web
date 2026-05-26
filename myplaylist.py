import streamlit as st
import pandas as pd
import requests

# 1. 페이지 기본 설정 및 브라우저 탭 타이틀
st.set_page_config(page_title="Weather Playlist", page_icon="🎧", layout="wide")

# 2. 스포티파이 스타일 커스텀 디자인 (CSS)
st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    .stSlider { color: #1DB954; }
    .song-card { 
        background-color: #181818; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 6px solid #1DB954; 
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .song-card:hover {
        background-color: #282828;
        border-left: 6px solid #1ed760;
    }
    .play-btn {
        background-color: #1DB954;
        color: black !important;
        padding: 10px 25px;
        border-radius: 25px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        font-size: 14px;
    }
    .play-btn:hover {
        background-color: #1ed760;
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

# 4. 사이드바 기상 시뮬레이터 구성
st.sidebar.title("📍 기상 시뮬레이터")

# 실시간 날씨 동기화 섹션
with st.sidebar.expander("🔍 실시간 날씨 연동", expanded=True):
    city_input = st.text_input("영문 도시명 입력", placeholder="Daejeon")
    if st.button("날씨 데이터 동기화"):
        if city_input:
            # 본인의 API 키를 입력하세요
            api_key = "5c55a17e72f6d32c9e75968bdd7beb19" 
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={city_input}&appid={api_key}&units=metric"
            try:
                res = requests.get(w_url).json()
                if res.get("cod") == 200:
                    st.session_state['temp'] = float(res['main']['temp'])
                    st.session_state['hum'] = float(res['main']['humidity'])
                    st.success(f"{city_input} 날씨 연동 완료!")
                else: st.error("도시를 찾을 수 없습니다.")
            except: st.error("연결 실패")

# 세션 상태 초기화 (슬라이더 연동용)
if 'temp' not in st.session_state: st.session_state['temp'] = 20.0
if 'hum' not in st.session_state: st.session_state['hum'] = 50.0

# 시뮬레이션 변수 조절
season = st.sidebar.selectbox("계절 설정", ["봄 (3-5월)", "여름 (6-8월)", "가을 (9-11월)", "겨울 (12-2월)", "전체 시즌"])
temp = st.sidebar.slider("온도 설정 (℃)", -20.0, 40.0, st.session_state['temp'], 0.1)
hum = st.sidebar.slider("습도 설정 (%)", 0.0, 100.0, st.session_state['hum'], 0.1)
vibe = st.sidebar.slider("나의 기분 (차분함 ↔ 신남)", 0.0, 100.0, 50.0, 0.1)

# 5. 메인 화면 출력
st.title("🎧 Weather Playlist v4.5")
st.write("사계절 빅데이터와 실시간 기상을 분석하여 당신에게 가장 필요한 음악 30곡을 추천합니다.")

if st.button("🚀 나만의 맞춤 플레이리스트 생성"):
    # 알고리즘 계산 (수치 매핑 및 가중치 모델)
    # 온도 기반 에너지 타겟
    t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
    # 습도 기반 밝기 타겟
    t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
    
    # 사계절 데이터 필터링 로직
    if "봄" in season: candidates = df[df['released_month'].isin([3, 4, 5])]
    elif "여름" in season: candidates = df[df['released_month'].isin([6, 7, 8])]
    elif "가을" in season: candidates = df[df['released_month'].isin([9, 10, 11])]
    elif "겨울" in season: candidates = df[df['released_month'].isin([12, 1, 2])]
    else: candidates = df
    
    candidates = candidates.copy()
    # 유클리드 거리 기반 오차 점수 산출
    candidates['score'] = (candidates['energy_%'] - t_e).abs() + (candidates['valence_%'] - t_v).abs()
    # 상위 30곡 정렬
    results = candidates.sort_values(by='score').head(30)
    
    st.info(f"✅ 분석 결과: {season} 음악 중 에너지 {t_e:.1f}% | 밝기 {t_v:.1f}%에 가장 근접한 상위 30곡입니다.")
    
    # 6. 결과 리스트 출력 (스포티파이 연동 카드)
    for i, (idx, row) in enumerate(results.iterrows()):
        # 스포티파이 다이렉트 플레이어 검색 링크 생성
        play_url = f"https://open.spotify.com/search/{row['track_name']} {row['artist(s)_name']}".replace(" ", "%20")
        
        st.markdown(f"""
            <div class="song-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #b3b3b3; font-size: 13px;">RANK {i+1}</span><br>
                        <b style="font-size: 20px;">{row['track_name']}</b><br>
                        <span style="color: #1DB954; font-size: 16px;">{row['artist(s)_name']}</span>
                    </div>
                    <div style="text-align: right;">
                        <small style="color: #b3b3b3;">에너지: {row['energy_%']}% | 밝기: {row['valence_%']}% | BPM: {row['bpm']}</small><br>
                        <a href="{play_url}" target="_blank" class="play-btn">▶ PLAY</a>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)