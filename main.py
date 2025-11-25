import requests
import json
import datetime
import re
import os
from collections import Counter
import urllib.parse

# === 설정: 고급 키워드 위주 검색 ===
SEARCH_KEYWORDS = [
    "부산 현지인 맛집", "부산 미쉐린 가이드", "부산 블루리본 맛집", 
    "부산 기장 찐맛집", "부산 영도 흰여울길 맛집", "부산 광안리 오션뷰 카페", 
    "부산 해운대 암소갈비", "부산 전포동 카페거리", "부산 깡통시장 먹거리"
]
MAX_RESULTS = 50

API_KEY = os.environ.get('YOUTUBE_API_KEY')

def clean_korean_text(text):
    # 1. [강력 차단] 영어, 숫자, 특수문자 아예 삭제 (순수 한글만 남김)
    # ENG, Vlog, 4K, 11, 60번 등 원천 봉쇄
    text = re.sub(r'[a-zA-Z0-9]', ' ', text)
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    
    words = text.split()
    cleaned_words = []
    
    # 2. [블랙리스트] 의미 없는 동사, 형용사, 부사 대거 추가
    garbage = set([
        # 지역/광범위 명사
        "부산", "한국", "경남", "전국", "지역", "동네", "국내",
        # 유튜브 상투어
        "맛집", "여행", "관광", "투어", "후기", "리뷰", "브이로그", "먹방", "영상", 
        "채널", "구독", "좋아요", "알람", "설정", "공개", "특집", "모음", "총정리",
        "비교", "분석", "소개", "추천", "강추", "방문", "탐방", "도전",
        # 무의미한 수식어
        "진짜", "정말", "완전", "대박", "역대급", "최고", "유명한", "솔직", "숨은", 
        "나만", "알고싶은", "비밀", "가성비", "저렴한", "비싼", "존맛", "꿀맛", 
        "미친", "개쩌는", "무조건", "절대", "실패", "없는", "성공", "인생",
        # 시간/장소 지칭
        "오늘", "지금", "어제", "내일", "주말", "평일", "시간", "위치", "가격", 
        "주차", "예약", "웨이팅", "여기", "저기", "거기", "어디", "곳은", "곳이", 
        "가장", "제일", "바로", "역시", "혹시", "무려", "특히",
        # 동사/형용사 활용형 (가장 지저분한 부분)
        "가는", "오는", "먹는", "보는", "하는", "있는", "없는", "가본", "먹어본", 
        "해본", "가세요", "오세요", "보세요", "드세요", "갑니다", "옵니다", "합니다", 
        "됩니다", "입니다", "있습니다", "없습니다", "같아요", "많은", "좋은", "나쁜",
        "가봤", "와봤", "먹봤", "해봤", "갔다", "왔다", "먹었다", "했다", "된다",
        "이거", "저거", "그거", "이걸", "저걸", "그걸", "무엇", "어떤", "어떻게",
        "알려주", "말해주", "보여주", "궁금해", "괜찮", "비주얼", "분위기",
        # 기타 잡다한 명사
        "사람", "현지인", "토박이", "외국인", "커플", "가족", "친구", "혼자", "남자", "여자",
        "데이트", "코스", "여행지", "명소", "핫플", "정보", "꿀팁", "이유", "충격", "실화"
    ])
    
    # 3. 조사 및 어미 정밀 제거
    suffixes = [
        "은", "는", "이", "가", "을", "를", "에", "의", "서", "로", "와", "과", "도", "만", 
        "이나", "나", "랑", "이랑", "까지", "부터", "에게", "께", "한테", "에서",
        "하고", "하며", "해서", "해", "고", "며", "요", "죠", "네요", "세요", 
        "우와", "인가", "인가요", "인지", "던", "된", "될", "할", "한"
    ]

    for w in words:
        word_to_add = w
        
        # 2글자 이상만 처리
        if len(word_to_add) > 1:
            # 접미사 반복 제거 (예: "부산에서는" -> "부산")
            original_word = word_to_add
            for _ in range(2): # 두 번까지 깎음
                for suffix in suffixes:
                    if word_to_add.endswith(suffix):
                        word_to_add = word_to_add[:-len(suffix)]
                        break
            
            # [최종 필터]
            # 1. 2글자 이상이어야 함 (한 글자짜리 '맛', '집' 등 제외)
            # 2. 불용어(garbage)에 없어야 함
            # 3. 원래 단어가 너무 짧아졌으면(1글자) 버림
            if len(word_to_add) >= 2 and word_to_add not in garbage:
                cleaned_words.append(word_to_add)
            
    return cleaned_words

def get_real_youtube_data():
    all_words = []
    
    if not API_KEY:
        return []

    print("🚀 프리미엄 데이터 필터링 중...")
    
    for keyword in SEARCH_KEYWORDS:
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
            
    # 상위 70개만 엄선 (너무 자잘한 건 뺌)
    return Counter(all_words).most_common(70)

try:
    word_counts = get_real_youtube_data()
except:
    word_counts = []

d3_data = []
if word_counts:
    max_count = word_counts[0][1]
    for word, count in word_counts:
        # 클릭시 검색어 최적화
        search_query = f"부산 {word} 추천" 
        encoded_query = urllib.parse.quote(search_query)
        link = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        size = 15 + (count / max_count) * 90
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
                overflow: auto; 
                font-family: 'Noto Sans KR', sans-serif;
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                min-height: 100vh;
            }
            #container { width: 100%; height: auto; display: flex; flex-direction: column; align-items: center; padding: 20px 0; }
            h2 { 
                color: #006064; margin: 10px 0 5px 0; 
                font-family: 'Black Han Sans', sans-serif; 
                font-size: 3em; 
                text-shadow: 2px 2px 0px #fff;
            }
            .footer { font-size: 0.9em; color: #555; margin-bottom: 20px; font-weight: bold; }
            .word-link { cursor: pointer; transition: all 0.2s ease; }
            .word-link:hover { opacity: 0.7 !important; text-shadow: 1px 1px 5px rgba(255,255,255,0.8); }
            
            #cloud-area { width: 100%; flex-grow: 1; display: flex; align-items: center; justify-content: center; }
            
            svg { width: 95%; height: auto; max-width: 1200px; display: block; }
        </style>
    </head>
    <body>
        <div id="container">
            <h2>🌊 부산 찐맛집 & 핫플 지도</h2>
            <p class="footer">Premium Info Analysis • Updated: __DATE_PLACEHOLDER__</p>
            <div id="cloud-area"></div>
        </div>

        <script>
            var words = __DATA_PLACEHOLDER__;
            var myColor = d3.scaleOrdinal().range(["#01579b", "#0288d1", "#00acc1", "#00bfa5", "#ff6f00", "#d84315", "#c2185b"]);

            var layoutWidth = 1000;
            var layoutHeight = 800; 

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
                  .text(function(d) { return d.text + " (Click for Info)"; });
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
