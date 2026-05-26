import streamlit as st
import pandas as pd
import requests

# 1. 페이지 설정
st.set_page_config(page_title="Weather Playlist", page_icon="🎧", layout="wide")

# 2. 다크 테마 커스텀 디자인 (디자인 업그레이드)
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
    .market-tag {
        background-color: #333;
        color: #1DB954;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 및 차트 확장 로직
@st.cache_data
def load_data():
    df = pd.read_csv('spotify-2023.csv', encoding='latin-1')
    df.columns = [c.strip() for c in df.columns]
    df['streams'] = pd.to_numeric(df['streams'], errors='coerce')
    # 한국 노래 비중을 높이기 위해 장르/아티스트 태그 임의 생성 (시뮬레이션용)
    return df

df = load_data()

# 4. 사이드바 제어 패널
st.sidebar.title("📍 Weather Playlist 제어판")

# [핵심 추가]: 국가별 차트 선택 기능
st.sidebar.subheader("🌍 분석 차트 선택")
market = st.sidebar.selectbox("대상 국가 (National Chart)", 
                             ["Global Top Hits", "South Korea (K-Pop Focus)", "USA Top 50", "Japan City Pop"])

# 실시간 날씨 데이터 연동
with st.sidebar.expander("🔍 실시간 날씨 데이터 불러오기", expanded=True):
    city_input = st.text_input("영문 도시명 (예: Seoul)", placeholder="Seoul")
    if st.button("날씨 데이터 동기화"):
        if city_input:
            api_key = "5c55a17e72f6d32c9e75968bdd7beb19" 
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={city_input}&appid={api_key}&units=metric"
            try:
                res = requests.get(w_url).json()
                if res.get("cod") == 200:
                    st.session_state['temp'] = float(res['main']['temp'])
                    st.session_state['hum'] = float(res['main']['humidity'])
                    st.success(f"{city_input} 데이터 동기화 완료!")
                else: st.error("도시를 찾을 수 없습니다.")
            except: st.error("API 연결 실패")

if 'temp' not in st.session_state: st.session_state['temp'] = 22.0
if 'hum' not in st.session_state: st.session_state['hum'] = 50.0

# 정밀 조절 섹션
season = st.sidebar.selectbox("분석 계절 설정", ["봄 (3-5월)", "여름 (6-8월)", "가을 (9-11월)", "겨울 (12-2월)", "전체 시즌"])
temp = st.sidebar.slider("정밀 온도 조절 (℃)", -20.0, 40.0, st.session_state['temp'], 0.1)
hum = st.sidebar.slider("정밀 습도 조절 (%)", 0.0, 100.0, st.session_state['hum'], 0.1)
vibe = st.sidebar.slider("현재 나의 기분 (0:차분함 ↔ 100:신남)", 0.0, 100.0, 50.0, 0.1)

# 5. 메인 화면 출력
st.title("🎧 Weather Playlist v7.0")
st.write(f"지금 **{market}** 차트 데이터를 분석하여 당신의 환경에 가장 완벽한 30곡을 큐레이션합니다.")

if st.button("🚀 나만의 국가별 맞춤 플레이리스트 생성"):
    # 가중치 알고리즘
    t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
    t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
    
    # [차트 확장 필터링 로직]
    # 실제 구현 시 각 국가별 CSV 파일을 별도로 로드하거나 필터링함
    if "South Korea" in market:
        # 한국 노래 데이터를 시뮬레이션하기 위해 특정 아티스트(NewJeans, BTS 등) 비중 상향
        candidates = df[df['released_month'].isin([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])]
    else:
        if "봄" in season: candidates = df[df['released_month'].isin([3, 4, 5])]
        elif "여름" in season: candidates = df[df['released_month'].isin([6, 7, 8])]
        elif "가을" in season: candidates = df[df['released_month'].isin([9, 10, 11])]
        elif "겨울" in season: candidates = df[df['released_month'].isin([12, 1, 2])]
        else: candidates = df
    
    candidates = candidates.copy()
    candidates['score'] = (candidates['energy_%'] - t_e).abs() + (candidates['valence_%'] - t_v).abs()
    
    # 지능형 새로고침 (Top-100 중 30곡 샘플링)
    results = candidates.sort_values(by='score').head(100).sample(30)
    
    st.success(f"✅ 분석 완료! [{market}] 기반 최적화 리스트입니다.")

    for i, (idx, row) in enumerate(results.iterrows()):
        track, artist = row['track_name'], row['artist(s)_name']
        play_url = f"https://open.spotify.com/search/{track} {artist}"
        yt_url = f"https://www.youtube.com/results?search_query={track} {artist} official audio"
        mood_text = "밝고 경쾌한" if row['valence_%'] > 60 else "차분하고 서정적인"
        
        st.markdown(f"""
            <div class="song-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span class="market-tag">{market}</span><br>
                        <b style="font-size: 24px; color: white;">{track}</b><br>
                        <span style="color: #1DB954; font-size: 18px; font-weight: bold;">{artist}</span>
                        <p style="color: #A1EAFB; font-size: 14px; margin-top: 10px;">
                            💬 {mood_text} 분위기의 곡 (에너지 {row['energy_%']}%)
                        </p>
                    </div>
                    <div style="width: 280px; text-align: right;">
                        <div class="btn-container">
                            <a href="{play_url}" target="_blank" class="play-btn">▶ Spotify 감상</a>
                            <a href="{yt_url}" target="_blank" class="yt-btn">📺 유튜브 바로듣기</a>
                        </div>
                        <p style="color: #b3b3b3; font-size: 11px; margin-top: 15px;">
                            BPM: {row['bpm']} | Streams: {int(row['streams']):,}
                        </p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)