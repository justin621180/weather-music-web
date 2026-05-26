import streamlit as st
import pandas as pd
import requests

# 1. 페이지 기본 설정
st.set_page_config(page_title="Weather Playlist", page_icon="🎧", layout="wide")

# 2. 스포티파이 & 유튜브 테마 커스텀 디자인 (CSS)
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
    }
    .btn-container { display: flex; gap: 10px; margin-top: 15px; }
    .play-btn {
        background-color: #1DB954;
        color: black !important;
        padding: 10px 20px;
        border-radius: 20px;
        text-decoration: none;
        font-weight: bold;
        font-size: 13px;
        flex: 1;
        text-align: center;
    }
    .yt-btn {
        background-color: #FF0000;
        color: white !important;
        padding: 10px 20px;
        border-radius: 20px;
        text-decoration: none;
        font-weight: bold;
        font-size: 13px;
        flex: 1;
        text-align: center;
    }
    .play-btn:hover, .yt-btn:hover { opacity: 0.8; transform: scale(1.02); }
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

# 4. 사이드바 제어 패널
st.sidebar.title("📍 Weather Playlist Control")

# [기능] 실시간 날씨 연동
with st.sidebar.expander("🔍 실시간 날씨 데이터 동기화", expanded=True):
    city_input = st.text_input("영문 도시명 입력 (예: Seoul)", placeholder="Seoul")
    if st.button("날씨 데이터 불러오기"):
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

if 'temp' not in st.session_state: st.session_state['temp'] = 22.0
if 'hum' not in st.session_state: st.session_state['hum'] = 50.0

# [기능] 사계절 및 정밀 수치 시뮬레이터
season = st.sidebar.selectbox("분석 계절 설정", ["봄 (3-5월)", "여름 (6-8월)", "가을 (9-11월)", "겨울 (12-2월)", "전체 시즌"])
temp = st.sidebar.slider("정밀 온도 조절 (℃)", -20.0, 40.0, st.session_state['temp'], 0.1)
hum = st.sidebar.slider("정밀 습도 조절 (%)", 0.0, 100.0, st.session_state['hum'], 0.1)
vibe = st.sidebar.slider("현재 나의 기분 (0:차분함 ↔ 100:신남)", 0.0, 100.0, 50.0, 0.1)

# 5. 메인 화면
st.title("🎧 Weather Playlist v6.0")
st.write("기상 데이터와 스트리밍 빅데이터를 융합하여 당신의 환경에 가장 완벽한 음악 30곡을 큐레이션합니다.")

# [기능] 지능형 새로고침 버튼
if st.button("🚀 나만의 플레이리스트 생성 및 새로고침"):
    # 가중치 알고리즘
    t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
    t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
    
    if "봄" in season: candidates = df[df['released_month'].isin([3, 4, 5])]
    elif "여름" in season: candidates = df[df['released_month'].isin([6, 7, 8])]
    elif "가을" in season: candidates = df[df['released_month'].isin([9, 10, 11])]
    elif "겨울" in season: candidates = df[df['released_month'].isin([12, 1, 2])]
    else: candidates = df
    
    candidates = candidates.copy()
    candidates['score'] = (candidates['energy_%'] - t_e).abs() + (candidates['valence_%'] - t_v).abs()
    
    # 상위 100곡 중 30곡 랜덤 샘플링
    results = candidates.sort_values(by='score').head(100).sample(30)
    
    st.info(f"✅ 분석 완료! {season} 테마 | 기온 {temp}℃, 습도 {hum}% 에 최적화된 새로운 음악 조합입니다.")

    # 6. 결과 출력 (스포티파이 + 유튜브 더블 연동)
    for i, (idx, row) in enumerate(results.iterrows()):
        track, artist = row['track_name'], row['artist(s)_name']
        
        # 스포티파이 다이렉트 링크
        play_url = f"https://open.spotify.com/search/{track} {artist}"
        # 유튜브 미리보기(검색) 링크
        yt_url = f"https://www.youtube.com/results?search_query={track} {artist} official audio"
        
        st.markdown(f"""
            <div class="song-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span style="color: #b3b3b3; font-size: 12px;">AI SMART CURATION</span><br>
                        <b style="font-size: 22px;">{track}</b><br>
                        <span style="color: #1DB954; font-size: 17px; font-weight: bold;">{artist}</span>
                        <p style="color: #b3b3b3; font-size: 12px; margin-top: 10px;">
                            Energy: {row['energy_%']}% | Valence: {row['valence_%']}% | BPM: {row['bpm']}
                        </p>
                    </div>
                    <div style="width: 250px;">
                        <div class="btn-container">
                            <a href="{play_url}" target="_blank" class="play-btn">▶ Spotify 감상</a>
                            <a href="{yt_url}" target="_blank" class="yt-btn">📺 YouTube 미리듣기</a>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)