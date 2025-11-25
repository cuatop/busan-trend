import json
import datetime
import re
from collections import Counter
# 유튜브 검색 도구
from youtubesearchpython import VideosSearch

# === 설정 ===
SEARCH_KEYWORDS = ["부산 맛집", "부산 여행", "부산 핫플", "부산 카페", "Busan Food", "Busan Travel"]
MAX_RESULTS_PER_KEYWORD = 50 

def clean_korean_text(text):
    # 특수문자 제거
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    words = text.split()
    
    cleaned_words = []
    # 불용어 리스트
    garbage = [
        "부산", "맛집", "여행", "브이로그", "Vlog", "Korea", "Busan", "Food", "Mukbang", "먹방", 
        "추천", "코스", "진짜", "정말", "하는", "있는", "가볼만한곳", "Best", "Top", "존맛", 
        "영상", "오늘", "투어", "후기", "식당", "카페", "Cafe", "Street", "Review", "리뷰",
        "2024", "2025", "1박2일", "2박3일", "사람", "이유", "충격", "공개", "가지", "모음",
        "현지인", "솔직", "방문", "위치", "가격", "메뉴", "대박", "유명한", "웨이팅", "필수",
        "Eng", "Sub", "Japanese", "Korean", "Travel", "Trip", "나오", "여기"
    ]
    
    for w in words:
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
                    words = clean_korean_text(title)
                    all_words.extend(words)
        except Exception as e:
            print(f"Error: {e}")
            continue
            
    return Counter(all_words).most_common(80)

# === 데이터 수집 ===
try:
    word_counts = get_youtube_data()
except Exception as e:
    print(f"데이터 수집 중 오류: {e}")
    word_counts = []

# === HTML 템플릿 (안전한 문자열 방식) ===
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
        
        /* 반응형 꽉 찬 화면 설정 */
        #cloud-area { width: 100%; flex-grow: 1; display: flex; align-items: center; justify-content: center; }
        svg { width: 100%; height: 100%; display: block; }
    </style>
</head>
<body>
    <div id="container">
        <h2>🌊 부산 핫플레이스 & 맛집</h2>
        <p class="footer">YouTube Trend • Updated: __DATE_PLACEHOLDER__</p>
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
              .text(function(d) { return d.text + " (YouTube)"; });
        }
    </script>
</body>
</html>
"""

# === 데이터 주입 및 파일 저장 ===
if word_counts:
    d3_data = []
    max_count = word_counts[0][1] if word_counts else 1
    
    for word, count in word_counts:
        link = "https://www.youtube.com/results?search_query=부산+" + word
        size = 15 + (count / max_count) * 85
        d3_data.append({"text": word, "size": size, "url": link, "count": count})

    json_str = json.dumps(d3_data)
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    
    final_html = html_template.replace("__DATA_PLACEHOLDER__", json_str).replace("__DATE_PLACEHOLDER__", today_str)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("성공: index.html 생성 완료")
else:
    print("데이터 없음")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<h2>No Data Found</h2>")
