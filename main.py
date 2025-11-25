import requests
import json
import datetime
import re
import os
from collections import Counter
import urllib.parse

# === [수정 완료] 검색 키워드 변경 ===
# "부산 가볼만한곳" -> "부산 핫플"로 교체했습니다.
SEARCH_KEYWORDS = [
    "부산", "부산 맛집", "부산 관광", "부산 여행", 
    "부산 행사", "부산 페스티벌", "부산 축제", "부산 핫플"
]
MAX_RESULTS = 50

API_KEY = os.environ.get('YOUTUBE_API_KEY')

def clean_korean_text(text):
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    words = text.split()
    cleaned_words = []
    garbage = [
        "부산", "맛집", "여행", "브이로그", "Vlog", "Korea", "Busan", "Food", "Mukbang", "먹방", 
        "추천", "코스", "진짜", "정말", "하는", "있는", "가볼만한곳", "Best", "Top", "존맛", 
        "영상", "오늘", "투어", "후기", "식당", "카페", "Cafe", "Street", "Review", "리뷰",
        "2024", "2025", "1박2일", "2박3일", "사람", "이유", "충격", "공개", "가지", "모음",
        "현지인", "솔직", "방문", "위치", "가격", "메뉴", "대박", "유명한", "웨이팅", "필수",
        "총정리", "실패", "없는", "무조건", "Best5", "Best10", "내돈내산", "Eng", "Sub",
        "관광", "행사", "페스티벌", "축제", "Festival", "Trip", "Travel", "핫플"
    ]
    for w in words:
        if len(w) > 2:
            for josa in ["은", "는", "이", "가", "을", "를", "에", "의", "서", "로", "고", "하고", "에서", "이랑"]:
                if w.endswith(josa):
                    w = w[:-len(josa)]
                    break
        if len(w) >= 2 and w not in garbage:
            cleaned_words.append(w)
    return cleaned_words

def get_real_youtube_data():
    all_words = []
    
    if not API_KEY:
        print("🚨 오류: API 키가 없습니다! GitHub Secrets를 확인해주세요.")
        return []

    print("🚀 유튜브 API로 실시간 데이터를 긁어옵니다...")
    
    for keyword in SEARCH_KEYWORDS:
        print(f"- 검색중: {keyword}")
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={keyword}&key={API_KEY}&maxResults={MAX_RESULTS}&type=video&order=date"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if 'items' in data:
                for item in data['items']:
                    title = item['snippet']['title']
                    words = clean_korean_text(title)
                    all_words.extend(words)
            else:
                print(f"  -> 결과 없음: {data.get('error', {}).get('message')}")
                
        except Exception as e:
            print(f"  -> 접속 에러: {e}")
            continue
            
    return Counter(all_words).most_common(100)

# === 실행 ===
try:
    word_counts = get_real_youtube_data()
except Exception as e:
    print(f"실행 중 오류: {e}")
    word_counts = []

# === HTML 생성 ===
d3_data = []
if word_counts:
    max_count = word_counts[0][1]
    for word, count in word_counts:
        
        # 클릭하면 '부산 + 단어'로 검색된 유튜브 결과 페이지로 이동
        search_query = f"부산 {word}"
        encoded_query = urllib.parse.quote(search_query)
        link = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        size = 15 + (count / max_count) * 100
        d3_data.append({"text": word, "size": size, "url": link, "count": count})

    html_template = """
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
            body { 
                margin: 0; padding: 0; 
                background-color: #e0f7fa; 
                text-align: center; 
                overflow: hidden; 
                font-family: 'Noto Sans KR', sans-serif;
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                height: 100vh;
            }
            #container { 
                width: 100%; 
                height: 100%;
                display: flex; flex-direction: column; align-items: center; 
            }
            h2 { 
                color: #006064; margin: 20px 0 5px 0; 
                font-family: 'Black Han Sans', sans-serif; 
                font-size: 3em; 
                text-shadow: 2px 2px 0px #fff;
            }
            .footer { font-size: 1em; color: #555; margin-bottom: 10px; font-weight: bold; }
            .word-link { cursor: pointer; transition: all 0.2s ease; }
            .word-link:hover { opacity: 0.7 !important; }
            #cloud-area { width: 100%; flex-grow: 1; display: flex; align-items: center; justify-content: center; }
            svg { width: 100%; height: 100%; display: block; }
        </style>
    </head>
    <body>
        <div id="container">
            <h2>🌊 부산 핫플레이스 & 맛집</h2>
            <p class="footer">Real-time YouTube Trend • Updated: __DATE_PLACEHOLDER__</p>
            <div id="cloud-area"></div>
        </div>

        <script>
            var words = __DATA_PLACEHOLDER__;
            var myColor = d3.scaleOrdinal().range(["#01579b", "#0288d1", "#00acc1", "#00bfa5", "#ff6f00", "#d84315", "#c2185b"]);

            var layoutWidth = 1000;
            var layoutHeight = 600;

            var layout = d3.layout.cloud()
                .size([layoutWidth, layoutHeight])
                .words(words.map(function(d) { return {text: d.text, size: d.size, url: d.url, count: d.count}; }))
                .padding(5) 
                .rotate(function() { return (~~(Math.random() * 6) - 3) * 30; })
                .font("Noto Sans KR")
                .fontWeight("900")
                .fontSize(function(d) { return d.size; })
                .on("end", draw);

            layout.start();

            function draw(words) {
              d3.select("#cloud-area").append("svg")
                  .attr("viewBox", "0 0 " + layoutWidth + " " + layoutHeight)
                  .attr("preserveAspectRatio", "xMidYMid meet")
                .append("g")
                  .attr("transform", "translate(" + layoutWidth / 2 + "," + layoutHeight / 2 + ")")
                .selectAll("text")
                  .data(words)
                .enter().append("text")
                  .attr("class", "word-link")
                  .style("font-size", function(d) { return d.size + "px"; })
                  .style("font-family", "'Noto Sans KR', sans-serif")
                  .style("font-weight", "900")
                  .style("fill", function(d, i) { return myColor(i); })
                  .attr("text-anchor", "middle")
                  .attr("transform", function(d) {
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                  })
                  .text(function(d) { return d.text; })
                  .on("click", function(d) { window.open(d.url, '_blank'); })
                  .append("title")
                  .text(function(d) { return "Click to search: " + d.text; });
            }
        </script>
    </body>
    </html>
    """

    json_str = json.dumps(d3_data)
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    final_html = html_template.replace("__DATA_PLACEHOLDER__", json_str).replace("__DATE_PLACEHOLDER__", today_str)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("성공: index.html 생성 완료")
else:
    print("데이터 없음")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<h2>데이터를 가져오지 못했습니다. API 키를 확인해주세요.</h2>")
