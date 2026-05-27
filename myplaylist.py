import streamlit as st
import pandas as pd
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import unicodedata
import urllib.parse

# 1. 페이지 기본 설정 및 브라우저 타이틀
st.set_page_config(page_title="Weather Playlist", page_icon="🎧", layout="wide")

# 2. 스포티파이 & 유튜브 스타일 커스텀 디자인 (CSS)
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
    .play-btn {
        background-color: #1DB954; color: black !important; padding: 10px 20px;
        border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 13px;
        display: inline-block; text-align: center; width: 100px;
    }
    .yt-btn {
        background-color: #FF0000; color: white !important; padding: 10px 20px;
        border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 13px;
        display: inline-block; text-align: center; width: 100px;
    }
    .play-btn:hover { background-color: #1ed760; }
    .yt-btn:hover { background-color: #cc0000; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 스포티파이 API 설정 (본인의 정보를 입력하세요)
# ---------------------------------------------------------
CLIENT_ID = "823102be1731465f88b1170f8f063b4f"
CLIENT_SECRET = "e636555833ce4f2098627d3e6415434b"

@st.cache_resource
def get_spotify_conn():
    try:
        auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        return spotipy.Spotify(auth_manager=auth_manager)
    except: return None

sp = get_spotify_conn()

# ---------------------------------------------------------
# 4. 데이터 정제 및 수집 함수 (인코딩 에러 방지)
# ---------------------------------------------------------
def safe_text(text):
    """한글 및 특수문자 처리를 위한 유니코드 정규화"""
    if text is None: return ""
    return unicodedata.normalize('NFC', str(text))

def get_live_chart(playlist_id):
    """Spotify API를 통한 실시간 차트 및 오디오 지수 수집"""
    if sp is None: return pd.DataFrame()
    try:
        results = sp.playlist_tracks(playlist_id)
        tracks = []
        for item in results['items']:
            t = item['track']
            if t:
                tracks.append({
                    'track_name': safe_text(t['name']),
                    'artist_name': safe_text(t['artists'][0]['name']),
                    'id': t['id']
                })
        
        # 오디오 지수(Energy, Valence 등) 실시간 쿼리
        ids = [t['id'] for t in tracks]
        features = sp.audio_features(ids)
        for i, f in enumerate(features):
            if f:
                tracks[i]['energy_%'] = f['energy'] * 100
                tracks[i]['valence_%'] = f['valence'] * 100
                tracks[i]['bpm'] = f['tempo']
            else:
                tracks[i]['energy_%'], tracks[i]['valence_%'], tracks[i]['bpm'] = 50, 50, 120
        return pd.DataFrame(tracks)
    except Exception as e:
        st.sidebar.error(f"차트 수집 오류: {e}")
        return pd.DataFrame()

@st.cache_data
def load_csv_data():
    """과거 2023 CSV 데이터 로드"""
    try:
        df = pd.read_csv('spotify-2023.csv', encoding='latin-1')
        df.columns = [c.strip() for c in df.columns]
        df['track_name'] = df['track_name'].apply(safe_text)
        df['artist(s)_name'] = df['artist(s)_name'].apply(safe_text)
        df['streams'] = pd.to_numeric(df['streams'], errors='coerce')
        df.rename(columns={'artist(s)_name': 'artist_name'}, inplace=True)
        return df
    except: return pd.DataFrame()

# ---------------------------------------------------------
# 5. 사이드바 제어 패널
# ---------------------------------------------------------
st.sidebar.title("📍 Weather Playlist Control")

# [핵심] 차트 소스 선택
chart_mode = st.sidebar.selectbox("📊 분석 대상 차트 선택", 
    ["South Korea Top 50 (실시간)", "Global Top 50 (실시간)", "USA Top 50 (실시간)", "Local CSV (2023 히트곡)"])

chart_map = {
    "Global Top 50 (실시간)": "37i9dQZEVXbMDoHDw32t7L",
    "South Korea Top 50 (실시간)": "37i9dQZEVXbJZGli0uRm3C",
    "USA Top 50 (실시간)": "37i9dQZEVXbLRQvOuyv9Xw"
}

# 날씨 동기화
if 'temp' not in st.session_state: st.session_state['temp'] = 22.0
if 'hum' not in st.session_state: st.session_state['hum'] = 50.0

with st.sidebar.expander("🔍 실시간 날씨 데이터 연동", expanded=True):
    city = st.text_input("영문 도시명", placeholder="Seoul")
    if st.button("날씨 데이터 불러오기"):
        api_key = "5c55a17e72f6d32c9e75968bdd7beb19" # OpenWeatherMap API 키
        res = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric").json()
        if res.get("cod") == 200:
            st.session_state['temp'], st.session_state['hum'] = res['main']['temp'], res['main']['humidity']
            st.success(f"{city} 날씨 연동 성공!")

# 정밀 시뮬레이터 슬라이더
season = st.sidebar.selectbox("계절 필터 (CSV 전용)", ["봄", "여름", "가을", "겨울", "전체"])
temp = st.sidebar.slider("정밀 온도 설정 (℃)", -20.0, 40.0, st.session_state['temp'], 0.1)
hum = st.sidebar.slider("정밀 습도 설정 (%)", 0.0, 100.0, st.session_state['hum'], 0.1)
vibe = st.sidebar.slider("사용자 기분 (0:차분함 ↔ 100:신남)", 0.0, 100.0, 50.0, 0.1)

# ---------------------------------------------------------
# 6. 메인 로직 및 추천 실행
# ---------------------------------------------------------
st.title("🎧 Weather Playlist v8.2")
st.write(f"현재 **{chart_mode}** 데이터를 기반으로 당신의 감성에 최적화된 30곡을 큐레이션합니다.")

if st.button("🚀 분석 및 플레이리스트 생성 (새로고침)"):
    if sp is None:
        st.error("스포티파이 API 인증 정보가 없습니다. 코드를 확인하세요.")
    else:
        with st.spinner('실시간 차트 분석 중...'):
            # 데이터 로드
            if "실시간" in chart_mode:
                df = get_live_chart(chart_map[chart_mode])
                sample_size = min(15, len(df))
            else:
                df = load_csv_data()
                if "봄" in season: df = df[df['released_month'].isin([3,4,5])]
                elif "여름" in season: df = df[df['released_month'].isin([6,7,8])]
                elif "가을" in season: df = df[df['released_month'].isin([9,10,11])]
                elif "겨울" in season: df = df[df['released_month'].isin([12,1,2])]
                sample_size = 30

            if not df.empty:
                # 가중치 알고리즘
                t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
                t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
                
                df['score'] = (df['energy_%'] - t_e).abs() + (df['valence_%'] - t_v).abs()
                results = df.sort_values(by='score').head(100)
                if len(results) >= sample_size:
                    results = results.sample(sample_size)
                
                st.info(f"✅ 분석 완료! 온도 {temp}℃, 습도 {hum}% 에 최적화된 리스트입니다.")

                for i, row in results.iterrows():
                    # [에러 방지 핵심]: 한글/특수문자 포함 쿼리를 URL 코드로 변환
                    query_text = f"{row['track_name']} {row['artist_name']}"
                    safe_query = urllib.parse.quote(query_text)
                    
                    play_url = f"https://open.spotify.com/search/{safe_query}"
                    yt_url = f"https://www.youtube.com/results?search_query={safe_query}+official"
                    
                    mood_text = "밝고 경쾌한" if row['valence_%'] > 60 else "차분하고 서정적인"
                    
                    st.markdown(f"""
                        <div class="song-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="flex: 3;">
                                    <b style="font-size: 20px;">{row['track_name']}</b><br>
                                    <span style="color: #1DB954; font-size: 16px; font-weight: bold;">{row['artist_name']}</span>
                                    <p style="color: #A1EAFB; font-size: 14px; margin-top: 10px;">
                                        💬 {mood_text} 분위기 (에너지 {row['energy_%']:.1f}% | 밝기 {row['valence_%']:.1f}%)
                                    </p>
                                </div>
                                <div style="flex: 1; text-align: right; display: flex; gap: 10px; justify-content: flex-end;">
                                    <a href="{play_url}" target="_blank" class="play-btn">Spotify</a>
                                    <a href="{yt_url}" target="_blank" class="yt-btn">YouTube</a>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.error("데이터를 가져오는 데 실패했습니다.")