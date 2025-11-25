import json
import datetime
import re
from collections import Counter
# 유튜브 검색 도구 (나중에 설치함)
from youtubesearchpython import VideosSearch

# === 설정 ===
SEARCH_KEYWORDS = ["부산 맛집", "부산 여행", "부산 핫플", "부산 카페", "Busan Food", "Busan Travel"]
MAX_RESULTS_PER_KEYWORD = 50 # 키워드당 검색할 영상 수

def clean_korean_text(text):
    # 1. 특수문자 제거 (한글, 영어, 숫자만 남김)
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    
    # 2. 띄어쓰기 기준 분리
    words = text.split()
    
    cleaned_words = []
    # 3. 의미 없는 단어(불용어) 리스트
    garbage = [
        "부산", "맛집", "여행", "브이로그", "Vlog", "Korea", "Busan", "Food", "Mukbang", "먹방", 
        "추천", "코스", "진짜", "정말", "하는", "있는", "가볼만한곳", "Best", "Top", "존맛", 
        "영상", "오늘", "투어", "후기", "식당", "카페", "Cafe", "Street", "Review", "리뷰",
        "2024", "2025", "1박2일", "2박3일", "사람", "이유", "충격", "공개", "가지", "모음",
        "현지인", "솔직", "방문", "위치", "가격", "메뉴", "대박", "유명한", "웨이팅", "필수",
        "Eng", "Sub", "Japanese", "Korean", "Travel", "Trip", "나오", "여기"
    ]
    
    for w in words:
        # 간단한 조사 제거 (완벽하진 않지만 효과적)
        if len(w) > 2:
            for josa in ["은", "는", "이", "가", "을", "를", "에", "의", "서", "로", "고", "하고"]:
                if w.endswith(josa):
                    w = w[:-len(josa)]
                    break
        
        if len(w) >= 2 and w not in garbage:
            cleaned_words.append(w)
            
    return cleaned_words

def get_youtube_data():
    all_words = []
    print("유튜브 검색 시작...")
    
    for keyword in SEARCH_KEYWORDS:
        print(f"- 검색어: {keyword}")
        try:
            videosSearch = VideosSearch(keyword, limit=MAX_RESULTS_PER_KEYWORD)
            results = videosSearch.result()
            
            if 'result' in results:
                for video in results['result']:
                    title = video['title']
                    # 제목에서 단어 추출
                    words = clean_korean_text(title)
                    all_words.extend(words)
        except Exception as e:
            print(f"Error: {e}")
            continue
            
    # 상위 80개 단어 추출
    return Counter(all_words).most_common(80)

# === 데이터 수집 및 HTML 생성 ===
word_counts = get_youtube_data()

if word_counts:
    d3_data = []
    max_count = word_counts[0][1] if word_counts else 1
    
    for word, count in word_counts:
        # 유튜브 검색 링크 생성
        link = "https://www.youtube.com/results?search_query=부산+" + word
        # 글자 크기 (15~100)
        size = 15 + (count / max_count) * 85
        d3_data.append({"text": word, "size": size, "url": link, "count": count})

    # HTML 템플릿 (반응형 + 꽉 찬 화면)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Busan Hot Trends</title>
        <script src="https://d3js.org/d3.v5.min.js"></script>
        <script src="https://cdn.jsdelivr.net/gh/holtzy/D3-graph-gallery@master/LIB/d3.layout.cloud.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            body {{ 
                margin: 0; padding: 0; 
                background-color: #e0f7fa; /* 시원한 부산 바다색 배경 */
                text-align: center; 
                overflow: hidden; 
                font-family: 'Noto Sans KR', sans-serif;
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                height: 100vh;
            }}
            #container {{ width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; }}
            h2 {{ 
                color: #006064; margin: 20px 0 5px 0; 
                font-family: 'Black Han Sans', sans-serif; 
                font-size: 3em; 
                text-shadow: 2px 2px 0px #fff;
            }}
            .footer {{ font-size: 1em; color: #555; margin-bottom: 10px; font-weight: bold; }}
            .word-link {{ cursor: pointer; transition: all 0.2s ease; }}
            .word-link:hover {{ opacity: 0.7 !important; }}
            
            #cloud-area {{ width: 100%; flex-grow: 1; display: flex; align-items: center; justify-content: center; }}
            svg {{ width: 100%; height: 100%; display: block; }}
        </style>
    </head>
    <body>
        <div id="container">
            <h2>🌊 부산 핫플레이스 & 맛집</h2>
            <p class="footer">YouTube Trend • Updated: {datetime.date.today().strftime('%Y-%m-%d')}</p>
            <div id="cloud-area"></div>
        </div>

        <script>
            var words = {json.dumps(d3_data)};
            // 부산 느낌 색상 팔레트 (파랑, 옥색, 노랑, 빨강)
            var myColor = d3.scaleOrdinal().range(["#01579b", "#0288d1", "#00acc1", "#00bfa5", "#ff6f00", "#d84315", "#c2185b"]);

            var layoutWidth = 1000;
            var layoutHeight = 600;

            var layout = d3.layout.cloud()
                .size([layoutWidth, layoutHeight])
                .words(words.map(function(d) {{ return {{text: d.text, size: d.size, url: d.url, count: d.count}}; }}))
                .padding(5) 
                .rotate(function() {{ return (~~(Math.random() * 6) - 3) * 30; }})
                .font("Noto Sans KR")
                .fontWeight("900")
                .fontSize(function(d) {{ return d.size; }})
                .on("end", draw);

            layout.start();

            function draw(words) {{
              d3.select("#cloud-area").append("svg")
                  .attr("viewBox", "0 0 " + layoutWidth + " " + layoutHeight)
                  .attr("preserveAspectRatio", "xMidYMid meet")
                .append("g")
                  .attr("transform", "translate(" + layoutWidth / 2 + "," + layoutHeight /
