import streamlit as st
import pandas as pd
import requests
import unicodedata
import urllib.parse
from functools import partial

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
        flex: 1; text-align: center;
    }
    .yt-btn {
        background-color: #FF0000; color: white !important; padding: 10px 20px;
        border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 13px;
        flex: 1; text-align: center;
    }
    .play-btn:hover { background-color: #1ed760; }
    .yt-btn:hover { background-color: #cc0000; }
    .streams-tag {
        color: #b3b3b3;
        font-size: 12px;
        font-weight: bold;
        background-color: #222;
        padding: 3px 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 데이터 로드 및 정제 함수 (인코딩 및 다국어 복원)
# ---------------------------------------------------------
def safe_text(text):
    """한글 및 특수문자 처리를 위한 유니코드 정규화"""
    if text is None: return ""
    return unicodedata.normalize('NFC', str(text))

@st.cache_data
def load_data():
    try:
        # 데이터 로드 (latin-1 인코딩)
        df = pd.read_csv('spotify-2023.csv', encoding='latin-1')
        
        # [데이터 정제]: 깨진 인코딩(Mojibake) 복구 로직
        def fix_text_encoding(text):
            if not isinstance(text, str): return text
            try:
                # latin-1로 잘못 읽힌 바이너리를 다시 utf-8로 디코딩하여 성조와 한글 복구
                return text.encode('latin-1').decode('utf-8')
            except:
                return text

        df['track_name'] = df['track_name'].apply(fix_text_encoding).apply(safe_text)
        df['artist(s)_name'] = df['artist(s)_name'].apply(fix_text_encoding).apply(safe_text)
        
        df.columns = [c.strip() for c in df.columns]
        # 스트리밍 횟수 숫자 데이터 변환
        df['streams'] = pd.to_numeric(df['streams'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"데이터 파일을 불러오는 중 오류가 발생했습니다: {e}")
        return None

df = load_data()

# ---------------------------------------------------------
# 4. 사이드바 제어 패널 구성
# ---------------------------------------------------------
st.sidebar.title("📍 Weather Playlist Control")

# [기능 1] 실시간 위치 및 날씨 데이터 동기화
if 'temp' not in st.session_state: st.session_state['temp'] = 22.0
if 'hum' not in st.session_state: st.session_state['hum'] = 50.0

with st.sidebar.expander("🔍 실시간 날씨 데이터 연동", expanded=True):
    city_input = st.text_input("영문 도시명 입력 (예: Seoul)", placeholder="Daejeon")
    if st.button("날씨 데이터 불러오기"):
        if city_input:
            # [주의] 본인의 API 키를 여기에 입력하세요
            api_key = "5c55a17e72f6d32c9e75968bdd7beb19" 
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q={city_input}&appid={api_key}&units=metric"
            try:
                res = requests.get(w_url).json()
                if res.get("cod") == 200:
                    st.session_state['temp'] = float(res['main']['temp'])
                    st.session_state['hum'] = float(res['main']['humidity'])
                    st.success(f"{city_input} 데이터 동기화 완료!")
                else: st.error("도시를 찾을 수 없습니다.")
            except: st.error("API 서버 연결 실패")

# [기능 2] 사계절 및 정밀 수치 시뮬레이터
season = st.sidebar.selectbox("분석 계절 설정", ["전체", "봄 (3-5월)", "여름 (6-8월)", "가을 (9-11월)", "겨울 (12-2월)"])
temp = st.sidebar.slider("정밀 온도 조절 (℃)", -20.0, 40.0, st.session_state['temp'], 0.1)
hum = st.sidebar.slider("정밀 습도 조절 (%)", 0.0, 100.0, st.session_state['hum'], 0.1)
vibe = st.sidebar.slider("현재 나의 기분 (0:차분함 ↔ 100:신남)", 0.0, 100.0, 50.0, 0.1)

# ---------------------------------------------------------
# 5. 메인 화면 및 알고리즘 실행
# ---------------------------------------------------------
st.title("🎧 Weather Playlist v7.6")
st.write("빅데이터 분석과 실시간 기상을 융합하여 당신의 환경에 가장 완벽한 30곡을 큐레이션합니다.")

# [기능 3] 지능형 새로고침 및 분석 버튼
if st.button("🚀 나만의 플레이리스트 생성 및 새로고침"):
    if df is not None:
        # 가중치 알고리즘 (날씨 60% + 사용자 기분 40%)
        t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
        t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
        
        # 사계절 데이터 필터링 로직
        if "봄" in season: candidates = df[df['released_month'].isin([3, 4, 5])]
        elif "여름" in season: candidates = df[df['released_month'].isin([6, 7, 8])]
        elif "가을" in season: candidates = df[df['released_month'].isin([9, 10, 11])]
        elif "겨울" in season: candidates = df[df['released_month'].isin([12, 1, 2])]
        else: candidates = df
        
        candidates = candidates.copy()
        # 수치 유사도 분석 (오차 점수 계산)
        candidates['score'] = (candidates['energy_%'] - t_e).abs() + (candidates['valence_%'] - t_v).abs()
        
        # [지능형 새로고침]: 상위 100곡 중 30곡 무작위 추출
        results = candidates.sort_values(by='score').head(100).sample(min(30, len(candidates)))
        
        st.info(f"✅ 분석 완료! 온도 {temp}℃, 습도 {hum}% 에 최적화된 플레이리스트입니다.")

        # 6. 결과 출력 (카드형 UI + 더블 플랫폼 연동)
        for i, (idx, row) in enumerate(results.iterrows()):
            track, artist = row['track_name'], row['artist(s)_name']
            
            # [에러 방지]: 특수문자/한글 포함 쿼리를 URL로 안전하게 인코딩
            query_text = f"{track} {artist}"
            safe_query = urllib.parse.quote(query_text)
            
            play_url = f"https://open.spotify.com/search/{safe_query}"
            yt_url = f"https://www.youtube.com/results?search_query={safe_query}+official+audio"
            
            # 곡 설명 생성 (NLG)
            mood_text = "밝고 경쾌한" if row['valence_%'] > 60 else "차분하고 서정적인"
            # 스트리밍 횟수 포맷팅 (콤마 추가)
            formatted_streams = "{:,}".format(int(row['streams']))
            
            st.markdown(f"""
                <div class="song-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 3;">
                            <b style="font-size: 22px; color: white;">{track}</b><br>
                            <span style="color: #1DB954; font-size: 18px; font-weight: bold;">{artist}</span>
                            <p style="color: #A1EAFB; font-size: 14px; margin-top: 10px;">
                                💬 {mood_text} 분위기 (에너지 {row['energy_%']}% | 밝기 {row['valence_%']}%)
                            </p>
                            <span class="streams-tag">🔥 총 {formatted_streams}회 스트리밍됨</span>
                        </div>
                        <div style="flex: 1; text-align: right;">
                            <div class="btn-container">
                                <a href="{play_url}" target="_blank" class="play-btn">Spotify</a>
                                <a href="{yt_url}" target="_blank" class="yt-btn">YouTube</a>
                            </div>
                            <p style="color: #b3b3b3; font-size: 11px; margin-top: 15px;">
                                BPM: {row['bpm']} | Release: {int(row['released_month'])}월
                            </p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.error("분석할 데이터를 가져오지 못했습니다. CSV 파일 위치를 확인하세요.")