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
        transition: 0.3s;
    }
    .song-card:hover {
        background-color: #282828;
        transform: translateY(-5px);
    }
    .btn-container { display: flex; gap: 10px; margin-top: 15px; }
    .play-btn {
        background-color: #1DB954; color: black !important; padding: 10px 20px;
        border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 13px;
        display: inline-block; text-align: center; flex: 1;
    }
    .yt-btn {
        background-color: #FF0000; color: white !important; padding: 10px 20px;
        border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 13px;
        display: inline-block; text-align: center; flex: 1;
    }
    .play-btn:hover { background-color: #1ed760; }
    .yt-btn:hover { background-color: #cc0000; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 스포티파이 API 설정 (본인의 정보를 입력하세요)
# ---------------------------------------------------------
# 스포티파이 대시보드에서 발급받은 키를 여기에 넣으세요
CLIENT_ID = "823102be1731465f88b1170f8f063b4f"
CLIENT_SECRET = "e636555833ce4f2098627d3e6415434b"

@st.cache_resource
def get_spotify_conn():
    if CLIENT_ID == "여러분의_CLIENT_ID": # 수정 안 했을 때 경고
        st.error("⚠️ 코드 상단의 CLIENT_ID를 실제 키로 바꿔주세요!")
        return None
    try:
        auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        return spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        st.error(f"⚠️ 스포티파이 인증 오류: {e}") # 진짜 에러 메시지 출력
        return None

sp = get_spotify_conn()

# ---------------------------------------------------------
# 4. 데이터 정제 및 수집 함수 (에러 방지 핵심)
# ---------------------------------------------------------
def safe_text(text):
    """한글, 성조, 특수문자를 유니코드 표준으로 복구 및 정규화"""
    if not isinstance(text, str): return str(text)
    try:
        # latin-1로 깨진 문자를 복구 시도
        text = text.encode('latin-1').decode('utf-8')
    except:
        pass
    return unicodedata.normalize('NFC', text)

def get_live_chart(playlist_id):
    """Spotify API를 통한 실시간 차트 데이터 수집"""
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
        
        # 오디오 피처(Energy, Valence 등) 실시간 수집
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
        st.sidebar.error(f"실시간 차트 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data
def load_csv_data():
    """과거 2023 CSV 데이터 로드 및 정제"""
    try:
        df = pd.read_csv('spotify-2023.csv', encoding='latin-1')
        df.columns = [c.strip() for c in df.columns]
        df['track_name'] = df['track_name'].apply(safe_text)
        df['artist(s)_name'] = df['artist(s)_name'].apply(safe_text)
        df['streams'] = pd.to_numeric(df['streams'], errors='coerce')
        df.rename(columns={'artist(s)_name': 'artist_name'}, inplace=True)
        return df
    except:
        return pd.DataFrame()

# ---------------------------------------------------------
# 5. 사이드바 제어 패널 구성
# ---------------------------------------------------------
st.sidebar.title("📍 Weather Playlist Control")

# 분석 대상 차트 선택
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
    city = st.text_input("영문 도시명 (예: Daejeon)", placeholder="Seoul")
    if st.button("날씨 데이터 불러오기"):
        api_key = "5c55a17e72f6d32c9e75968bdd7beb19" # 날씨 API 키
        w_res = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric").json()
        if w_res.get("cod") == 200:
            st.session_state['temp'], st.session_state['hum'] = w_res['main']['temp'], w_res['main']['humidity']
            st.success(f"{city} 날씨 연동 성공!")

# 세부 수치 시뮬레이터
season = st.sidebar.selectbox("계절 필터 (CSV 전용)", ["전체", "봄", "여름", "가을", "겨울"])
temp = st.sidebar.slider("정밀 온도 설정 (℃)", -20.0, 40.0, st.session_state['temp'], 0.1)
hum = st.sidebar.slider("정밀 습도 설정 (%)", 0.0, 100.0, st.session_state['hum'], 0.1)
vibe = st.sidebar.slider("현재 나의 기분 (0:차분함 ↔ 100:신남)", 0.0, 100.0, 50.0, 0.1)

# ---------------------------------------------------------
# 6. 메인 화면 및 알고리즘 실행
# ---------------------------------------------------------
st.title("🎧 Weather Playlist v8.3")
st.write(f"현재 **{chart_mode}** 데이터를 기반으로 당신의 환경에 최적화된 음악을 제안합니다.")

if st.button("🚀 분석 및 플레이리스트 생성 (새로고침)"):
    if sp is None and "실시간" in chart_mode:
        st.error("스포티파이 API 키를 코드에 입력해주세요.")
    else:
        with st.spinner('데이터를 분석 중입니다...'):
            # 데이터 로드 로직
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
                # 하이브리드 추천 알고리즘 (날씨 60% + 사용자 기분 40%)
                t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
                t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
                
                df['score'] = (df['energy_%'] - t_e).abs() + (df['valence_%'] - t_v).abs()
                
                # 지능형 새로고침 (Top-100 중 랜덤 샘플링)
                results = df.sort_values(by='score').head(100)
                if len(results) >= sample_size:
                    results = results.sample(sample_size)
                
                st.info(f"✅ 분석 완료! 온도 {temp}℃, 습도 {hum}% 최적화 결과입니다.")

                for i, row in results.iterrows():
                    # [에러 방지 핵심]: 특수문자/한글 포함 쿼리를 URL로 안전하게 인코딩
                    query_text = f"{row['track_name']} {row['artist_name']}"
                    safe_query = urllib.parse.quote(query_text)
                    
                    play_url = f"https://open.spotify.com/search/{safe_query}"
                    yt_url = f"https://www.youtube.com/results?search_query={safe_query}+official+audio"
                    
                    mood_text = "밝고 경쾌한" if row['valence_%'] > 60 else "차분하고 서정적인"
                    
                    st.markdown(f"""
                        <div class="song-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="flex: 3;">
                                    <b style="font-size: 22px; color: white;">{row['track_name']}</b><br>
                                    <span style="color: #1DB954; font-size: 18px; font-weight: bold;">{row['artist_name']}</span>
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
                st.error("분석할 데이터를 가져오지 못했습니다. API 설정 혹은 CSV 파일을 확인하세요.")