import requests
import json
import datetime
import re
import os
from collections import Counter
import urllib.parse

# === 설정 ===
SEARCH_KEYWORDS = [
    "부산 맛집", "부산 여행", "부산 관광", "부산 핫플", 
    "부산 가볼만한곳", "부산 축제", "부산 현지인 맛집", "부산 데이트"
]
MAX_RESULTS = 50

API_KEY = os.environ.get('YOUTUBE_API_KEY')

def clean_korean_text(text):
    # 1. 광고/스팸 필터링 (제목에 이런 단어 있으면 아예 버림)
    spam_keywords = ["광고", "협찬", "문의", "shorts", "Shorts", "쇼츠", "구독", "좋아요", "직캠", "공구"]
    for spam in spam_keywords:
        if spam in text:
            return []

    # 2. 특수문자 제거
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    words = text.split()
    
    cleaned_words = []
    # 3. 의미 없는 단어 대거 삭제 (순수 명사/지명 위주로 남기기 위함)
    garbage = set([
        "부산", "맛집", "여행", "브이로그", "Vlog", "Korea", "Busan", "Food", "Mukbang", "먹방", 
        "추천", "코스", "진짜", "정말", "하는", "있는", "가볼만한곳", "Best", "Top", "존맛", 
        "영상", "오늘", "투어", "후기", "식당", "카페", "Cafe", "Street", "Review", "리뷰",
        "2024", "2025", "1박2일", "2박3일", "사람", "이유", "충격", "공개", "가지", "모음",
        "현지인", "솔직", "방문", "위치", "가격", "메뉴", "대박", "유명한", "웨이팅", "필수",
        "총정리", "실패", "없는", "무조건", "Best5", "Best10", "내돈내산", "Eng", "Sub",
        "관광", "행사", "페스티벌", "축제", "Festival", "Trip", "Travel", "핫플", "데이트",
        "관리", "통제", "2부", "1부", "규모", "규묘", "amp", "그리고", "그래서", "하지만", 
        "가세요", "오세요", "먹고", "보고", "가서", "와서", "너무", "많이", "진심", "역대급",
        "한국", "일본", "세계", "최고", "분위기", "무료", "입장", "시간", "주차", "꿀팁"
    ])
    
    # 조사/어미 제거 리스트
    suffixes = ["은", "는", "이", "가", "을", "를", "에", "의", "서", "로", "고", "하고", "에서", "이랑", "까지", "부터", "으로", "네요", "세요", "우와", "인가", "인가요"]

    for w in words:
        word_to_add = w
        if len(word_to_add) > 2:
            for suffix in suffixes:
                if word_to_add.endswith(suffix):
                    word_to_add = word_to_add[:-len(suffix)]
                    break
        
        # 2글자 이상이고 블랙리스트에 없는 단어만 채택
        if len(word_to_add) >= 2 and word_to_add.lower() not in garbage:
            cleaned_words.append(word_to_add)
            
    return cleaned_words

def get_real_youtube_data():
    all_words = []
    
    if not API_KEY:
        return []

    print("🚀 고급 정보 필터링 중...")
    
    for keyword in SEARCH_KEYWORDS:
        # 조회수(viewCount) 순으로 정렬해서, 검증된 인기 영상 위주로 가져옴
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={keyword}&key={API_KEY}&maxResults={MAX_RESULTS}&type=video&order=viewCount"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if 'items' in data:
                for item in data['items']:
                    title = item['snippet']['title']
                    words = clean_korean_text(title)
                    all_words.extend(words)
        except: continue
            
    return Counter(all_words).most_common(80)

try:
    word_counts = get_real_youtube_data()
except:
    word_counts = []

d3_data = []
if word_counts:
    max_count = word_counts[0][1]
    for word, count in word_counts:
        # [핵심] 클릭 시 검색어 뒤에 '솔직후기 꿀팁'을 붙여서 검색
        # 이렇게 하면 광고나 쇼츠가 걸러지고 양질의 영상이 상단에 뜸
        search_query = f"부산 {word} 솔직후기 꿀팁" 
        encoded_query = urllib.parse.quote(search_query)
        link = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        size = 15 + (count / max_count) * 85
        d3_data.append({"text": word, "size": size, "url": link, "count": count})

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Busan Premium Trends</title>
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
            #container { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; }
            h2 { 
                color: #006064; margin: 20px 0 5px 0; 
                font-family: 'Black Han Sans', sans-serif; 
                font-size: 2.5em; 
                text-shadow: 2px 2px 0px #fff;
            }
            .footer { font-size: 0.9em; color: #555; margin-bottom: 10px; font-weight: bold; }
            .word-link { cursor: pointer; transition: all 0.2s ease; }
            .word-link:hover { opacity: 0.7 !important; text-shadow: 1px 1px 5px rgba(255,255,255,0.8); }
            #cloud-area { width: 100%; flex-grow: 1; display: flex; align-items: center; justify-content: center; }
            svg { width: 100%; height: 100%; display: block; }
        </style>
    </head>
    <body>
        <div id="container">
            <h2>🌊 부산 찐맛집 & 핫플 트렌드</h2>
            <p class="footer">Premium Info Analysis • Updated: __DATE_PLACEHOLDER__</p>
            <div id="cloud-area"></div>
        </div>

        <script>
            var words = __DATA_PLACEHOLDER__;
            var myColor = d3.scaleOrdinal().range(["#01579b", "#0288d1", "#00acc1", "#00bfa5", "#ff6f00", "#d84315", "#c2185b"]);

            // 캔버스 크기 넉넉하게 (잘림 방지)
            var layoutWidth = 1200;
            var layoutHeight = 800;

            var layout = d3.layout.cloud()
                .size([layoutWidth, layoutHeight])
                .words(words.map(function(d) { return {text: d.text, size: d.size, url: d.url, count: d.count}; }))
                .padding(6) // 간격 조금 더 줌 (가독성)
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
                  .text(function(d) { return d.text + " (클릭하면 솔직후기 영상으로 이동합니다)"; });
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
else:
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<h2>No Data Found</h2>")
