import streamlit as st
import pandas as pd
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from functools import partial

# 1. 페이지 설정
st.set_page_config(page_title="Weather Playlist", page_icon="🎧", layout="wide")

# 2. 스포티파이 & 유튜브 스타일 커스텀 디자인
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
    .song-card:hover { background-color: #282828; transform: translateY(-3px); }
    .btn-container { display: flex; gap: 10px; margin-top: 15px; }
    .play-btn {
        background-color: #1DB954; color: black !important; padding: 10px 20px;
        border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 13px; flex: 1; text-align: center;
    }
    .yt-btn {
        background-color: #FF0000; color: white !important; padding: 10px 20px;
        border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 13px; flex: 1; text-align: center;
    }
    .play-btn:hover { background-color: #1ed760; }
    .yt-btn:hover { background-color: #cc0000; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 스포티파이 API 설정 (본인의 정보를 입력하세요)
# ---------------------------------------------------------
CLIENT_ID = "여러분의_CLIENT_ID"
CLIENT_SECRET = "여러분의_CLIENT_SECRET"

try:
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
except:
    st.sidebar.error("스포티파이 API 키를 확인해주세요!")

# ---------------------------------------------------------
# 4. 데이터 로드 및 실시간 차트 수집 함수
# ---------------------------------------------------------
def fix_text(text):
    """다국어 성조 및 특수문자 복원 로직"""
    if not isinstance(text, str): return text
    try: return text.encode('latin-1').decode('utf-8')
    except: return text

@st.cache_data
def load_csv_data():
    df = pd.read_csv('spotify-2023.csv', encoding='latin-1')
    df['track_name'] = df['track_name'].apply(fix_text)
    df['artist(s)_name'] = df['artist(s)_name'].apply(fix_text)
    df.columns = [c.strip() for c in df.columns]
    df['streams'] = pd.to_numeric(df['streams'], errors='coerce')
    df.rename(columns={'artist(s)_name': 'artist_name'}, inplace=True)
    return df

def get_live_chart(playlist_id):
    """Spotify API를 통해 실시간 TOP 50 차트와 오디오 지수를 수집"""
    results = sp.playlist_tracks(playlist_id)
    tracks = []
    for item in results['items']:
        t = item['track']
        if t: tracks.append({'track_name': t['name'], 'artist_name': t['artists'][0]['name'], 'id': t['id'], 'released_month': 0})
    
    # 오디오 지수 실시간 쿼리
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

# ---------------------------------------------------------
# 5. 사이드바 제어 패널
# ---------------------------------------------------------
st.sidebar.title("📍 Weather Playlist Control")

# 차트 소스 선택
chart_mode = st.sidebar.selectbox("📊 분석 대상 차트 선택", 
    ["Global Top 50 (실시간)", "South Korea Top 50 (실시간)", "USA Top 50 (실시간)", "Local CSV (2023 히트곡)"])

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
        api_key = "5c55a17e72f6d32c9e75968bdd7beb19"
        res = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric").json()
        if res.get("cod") == 200:
            st.session_state['temp'], st.session_state['hum'] = res['main']['temp'], res['main']['humidity']
            st.success(f"{city} 날씨 동기화 완료!")

# 정밀 시뮬레이터 슬라이더
season = st.sidebar.selectbox("계절 필터 (CSV 전용)", ["봄", "여름", "가을", "겨울", "전체"])
temp = st.sidebar.slider("정밀 온도 설정 (℃)", -20.0, 40.0, st.session_state['temp'], 0.1)
hum = st.sidebar.slider("정밀 습도 설정 (%)", 0.0, 100.0, st.session_state['hum'], 0.1)
vibe = st.sidebar.slider("사용자 기분 (0:차분함 ↔ 100:신남)", 0.0, 100.0, 50.0, 0.1)

# ---------------------------------------------------------
# 6. 메인 화면 및 알고리즘 실행
# ---------------------------------------------------------
st.title("🎧 Weather Playlist v8.0")
st.write(f"현재 **{chart_mode}** 데이터를 기반으로 당신의 환경에 최적화된 30곡을 큐레이션합니다.")

if st.button("🚀 분석 및 플레이리스트 생성 (새로고침)"):
    with st.spinner('데이터를 분석하는 중...'):
        # 데이터 확보
        if "실시간" in chart_mode:
            df = get_live_chart(chart_map[chart_mode])
            sample_size = min(15, len(df)) # 실시간 차트는 곡수가 적어 상위 15곡만
        else:
            df = load_csv_data()
            if "봄" in season: df = df[df['released_month'].isin([3,4,5])]
            elif "여름" in season: df = df[df['released_month'].isin([6,7,8])]
            elif "가을" in season: df = df[df['released_month'].isin([9,10,11])]
            elif "겨울" in season: df = df[df['released_month'].isin([12,1,2])]
            sample_size = 30

        # 하이브리드 알고리즘 계산
        t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
        t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
        
        candidates = df.copy()
        candidates['score'] = (candidates['energy_%'] - t_e).abs() + (candidates['valence_%'] - t_v).abs()
        
        # 지능형 새로고침 적용
        results = candidates.sort_values(by='score').head(100)
        if len(results) >= sample_size:
            results = results.sample(sample_size)
        
        st.info(f"✅ 분석 완료! 온도 {temp}℃, 습도 {hum}% 최적화 결과입니다.")

        for i, row in results.iterrows():
            play_url = f"https://open.spotify.com/search/{row['track_name']} {row['artist_name']}"
            yt_url = f"https://www.youtube.com/results?search_query={row['track_name']}+{row['artist_name']}+official"
            mood_text = "밝고 경쾌한" if row['valence_%'] > 60 else "차분하고 서정적인"
            
            st.markdown(f"""
                <div class="song-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <b style="font-size: 22px;">{row['track_name']}</b><br>
                            <span style="color: #1DB954; font-size: 18px; font-weight: bold;">{row['artist_name']}</span>
                            <p style="color: #A1EAFB; font-size: 14px; margin-top: 10px;">
                                💬 {mood_text} 분위기 (에너지 {row['energy_%']:.1f}% | 밝기 {row['valence_%']:.1f}%)
                            </p>
                        </div>
                        <div style="width: 250px; text-align: right;">
                            <div class="btn-container">
                                <a href="{play_url}" target="_blank" class="play-btn">Spotify</a>
                                <a href="{yt_url}" target="_blank" class="yt-btn">YouTube</a>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)