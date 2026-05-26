import streamlit as st
import pandas as pd
import requests

# 페이지 제목과 아이콘
st.set_page_config(page_title="Weather Playlst", page_icon="🎧")

# 스포티파이 스타일 디자인 입히기
st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    .stSlider { color: #1DB954; }
    .song-card { background-color: #181818; padding: 20px; border-radius: 10px; border-left: 5px solid #1DB954; margin-bottom: 10px; }
    a { color: #1DB954 !important; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv('spotify-2023.csv', encoding='latin-1')
    df.columns = [c.strip() for c in df.columns]
    df['streams'] = pd.to_numeric(df['streams'], errors='coerce')
    return df

df = load_data()

# 사이드바 (설정창)
st.sidebar.title("📍 시뮬레이터 설정")
season = st.sidebar.selectbox("계절", ["여름 (6-8월)", "겨울 (12-2월)", "전체 시즌"])
temp = st.sidebar.slider("온도 (℃)", -20.0, 40.0, 25.0, 0.1)
hum = st.sidebar.slider("습도 (%)", 0.0, 100.0, 50.0, 0.1)
vibe = st.sidebar.slider("기분 (차분함 ↔ 신남)", 0.0, 100.0, 50.0, 0.1)

st.title("🎧 Weather Playlist v4.0")
st.write("당신의 현재 기상 조건과 감성을 분석해 최적의 음악을 추천합니다.")

if st.button("🚀 나만의 플레이리스트 생성하기"):
    # 알고리즘 계산
    t_e = ((temp + 20.0) * 1.5 * 0.6) + (vibe * 0.4)
    t_v = ((100.0 - hum * 0.8) * 0.6) + (vibe * 0.4)
    
    # 데이터 필터링
    if "여름" in season: candidates = df[df['released_month'].isin([6, 7, 8])]
    elif "겨울" in season: candidates = df[df['released_month'].isin([12, 1, 2])]
    else: candidates = df
    
    candidates = candidates.copy()
    candidates['score'] = (candidates['energy_%'] - t_e).abs() + (candidates['valence_%'] - t_v).abs()
    results = candidates.sort_values(by='score').head(30)
    
    st.info(f"분석 결과: 에너지 {t_e:.1f}% | 밝기 {t_v:.1f}%를 목표로 추천합니다.")
    
    # 결과 출력 (30곡)
    for i, (idx, row) in enumerate(results.iterrows()):
        url = f"https://open.spotify.com/search/{row['track_name'].replace(' ', '%20')}"
        st.markdown(f"""
            <div class="song-card">
                <span style="color: #b3b3b3;">RANK {i+1}</span><br>
                <b style="font-size: 18px;">{row['track_name']}</b> - {row['artist(s)_name']}<br>
                <small>에너지: {row['energy_%']}% | 밝기: {row['valence_%']}%</small><br>
                <a href="{url}" target="_blank">▶ Spotify에서 바로 듣기</a>
            </div>
        """, unsafe_allow_html=True)