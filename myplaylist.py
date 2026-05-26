import streamlit as st
import pandas as pd
import requests
import unicodedata # 발음 기호 제거를 위한 파이썬 내장 라이브러리

# 1. 페이지 기본 설정
st.set_page_config(page_title="Weather Playlist", page_icon="🎧", layout="wide")

# 2. 디자인 테마 (스포티파이 스타일)
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
        transform: translateY(-3px);
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
        
        # [핵심]: 성조/발음 기호를 가장 유사한 알파벳으로 변환하는 함수
        def normalize_text(text):
            if not isinstance(text, str): return text
            # 유니코드 분해 (예: 'é' -> 'e' + '´')
            text = unicodedata.normalize('NFD', text)
            # 분리된 기호들을 제외하고 알파벳만 남김, 깨진 특수문자 무시
            text = "".join([c for c in text if not unicodedata.combining(c)])
            return text.encode('ascii', 'ignore').decode('ascii')

        df['track_name'] = df['track_name'].apply(normalize_text)
        df['artist(s)_name'] = df['artist(s)_name'].apply(normalize_text)
        
        df.columns = [c.strip() for c in df.columns]
        df['streams'] = pd.to_numeric(df['streams'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return None

df = load_data()

# 4. 사이드바 제어 패널
st.sidebar.title("📍 Weather Playlist Control")

# 실시간 날씨 데이터 연동
with st.sidebar.expander("🔍 실시간 날씨 데이터 불러오기", expanded=True):
    city_input = st.text_input("영문 도시명 입력 (예: Seoul)", placeholder="Seoul")
    if st.button("날씨 동기화"):
        if city_input:
            # 본인의 API 키를 여기에 입력하세요
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

# 시뮬레이터 옵션
season = st.sidebar.selectbox("분석 계절 설정", ["봄 (3-5월)", "여름 (6-8월)", "가을 (9-11월)", "겨울 (12-2월)", "전체 시즌"])
temp = st.sidebar.slider("정밀 온도 조절 (℃)", -20.0, 40.0, st.session_state['temp'], 0.1)
hum = st.sidebar.slider("정밀 습도 조절 (%)", 0.0, 100.0, st.session_state['hum'], 0.1)
vibe = st.sidebar.slider("현재 나의 기분 (0:차분함 ↔ 100:신남)", 0.0, 100.0, 50.0, 0.1)

# 5. 메인 화면 출력
st.title("🎧 Weather Playlist v7.3")
st.write("알파벳 정규화 및 실시간 기상 API를 결합한 글로벌 음악 큐레이션 서비스입니다.")

# 분석 실행 버튼
if st.button("🚀 나만의 플레이리스트 생성 및 새로고침"):
    # 가중치 알고리즘
    t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
    t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
    
    # 계절 필터링
    if "봄" in season: candidates = df[df['released_month'].isin([3, 4, 5])]
    elif "여름" in season: candidates = df[df['released_month'].isin([6, 7, 8])]
    elif "가을" in season: candidates = df[df['released_month'].isin([9, 10, 11])]
    elif "겨울" in season: candidates = df[df['released_month'].isin([12, 1, 2])]
    else: candidates = df
    
    candidates = candidates.copy()
    candidates['score'] = (candidates['energy_%'] - t_e).abs() + (candidates['valence_%'] - t_v).abs()
    results = candidates.sort_values(by='score').head(100).sample(30)
    
    st.info(f"✅ 분석 완료! 온도 {temp}℃, 습도 {hum}% 에 최적화된 새로운 음악 조합입니다.")

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
                        <span style="color: #b3b3b3; font-size: 12px;">AI RECOMMENDATION</span><br>
                        <b style="font-size: 24px;">{track}</b><br>
                        <span style="color: #1DB954; font-size: 18px; font-weight: bold;">{artist}</span>
                        <p style="color: #A1EAFB; font-size: 14px; margin-top: 10px;">
                            💬 {mood_text} 분위기의 곡 (에너지 {row['energy_%']}%)
                        </p>
                    </div>
                    <div style="width: 260px; text-align: right;">
                        <div class="btn-container">
                            <a href="{play_url}" target="_blank" class="play-btn">▶ Spotify</a>
                            <a href="{yt_url}" target="_blank" class="yt-btn">📺 YouTube</a>
                        </div>
                        <p style="color: #b3b3b3; font-size: 11px; margin-top: 15px;">
                            BPM: {row['bpm']} | Streams: {int(row['streams']):,}
                        </p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)