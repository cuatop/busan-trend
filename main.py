import requests
import json
import datetime
import re
import os
from collections import Counter
import urllib.parse

# === 1. 검색어 고급화 (검색의 질을 높임) ===
# 단순히 "부산 여행"이 아니라, 알짜배기가 나올만한 검색어로 변경
SEARCH_KEYWORDS = [
    "부산 현지인 맛집", "부산 노포 맛집", "부산 미쉐린", "부산 블루리본",
    "부산 오션뷰 카페", "부산 숨은 명소", "부산 핫플 솔직후기", 
    "부산 기장 맛집", "부산 영도 맛집", "부산 광안리 찐맛집"
]
MAX_RESULTS = 50

API_KEY = os.environ.get('YOUTUBE_API_KEY')

def clean_korean_text(text):
    # 1. 유튜브 전용 잡다한 용어 사전 제거 (대소문자 무시)
    text_lower = text.lower()
    spam_terms = [
        "shorts", "vlog", "eng", "sub", "feat", "ep", "4k", "fhd", "hd", 
        "브이로그", "자막", "직캠", "티저", "공식", "하이라이트", "풀버전", 
        "광고", "협찬", "포함", "문의", "구독", "좋아요"
    ]
    for spam in spam_terms:
        if spam in text_lower:
            return [] # 광고나 잡다한 영상은 아예 분석 포기

    # 2. 특수문자 및 숫자 제거 (숫자가 섞인 잡다한 순위 제거: Top10, 3가지 등)
    # 순수 한글과 영어만 남김
    text = re.sub(r'[0-9]+', '', text) 
    text = re.sub(r'[^\w\s가-힣a-zA-Z]', ' ', text)
    
    words = text.split()
    cleaned_words = []
    
    # 3. [핵심] 프리미엄 불용어 필터 (잡다한 단어 강력 삭제)
    garbage = set([
        # 지역/국가 (너무 넓은 범위)
        "부산", "한국", "korea", "busan", "japan", "일본", "서울", "전국", "경상도",
        # 유튜브/여행 상투어
        "맛집", "여행", "관광", "투어", "후기", "리뷰", "review", "trip", "travel", "food", 
        "mukbang", "먹방", "음식", "식당", "카페", "cafe", "street", "road", "view",
        # 무의미한 형용사/동사/부사
        "진짜", "정말", "완전", "대박", "역대급", "최고", "best", "top", "hot", "new",
        "유명한", "솔직", "추천", "강추", "비밀", "숨은", "나만", "알고싶은", "공개",
        "가성비", "저렴한", "비싼", "존맛", "꿀맛", "미친", "개쩌는", "무조건", "절대",
        "가지", "곳은", "여기", "저기", "거기", "어디", "오늘", "지금", "근황", "일상",
        "하는", "있는", "가는", "오는", "먹는", "보는", "가본", "먹어본", "해본",
        "가세요", "오세요", "보세요", "갑니다", "옵니다", "합니다", "됩니다", "입니다",
        "사람", "현지인", "토박이", "외국인", "커플", "가족", "혼자", "데이트", "코스",
        "시간", "위치", "가격", "주차", "예약", "웨이팅", "정보", "꿀팁", "총정리", "모음",
        "실패", "성공", "이유", "충격", "실화", "특집", "편", "탄", "부", "호",
        "다시", "직접", "선정", "발견", "출연", "등장", "소개", "정리", "비교", "분석"
    ])
    
    # 조사 제거 리스트
    suffixes = ["은", "는", "이", "가", "을", "를", "에", "의", "서", "로", "고", "하고", "에서", "이랑", "까지", "부터", "으로", "네요", "세요", "우와", "인가", "인가요", "입니다", "습니다", "에도", "이나"]

    for w in words:
        word_to_add = w
        
        # 조사 제거
        if len(word_to_add) > 1:
            for suffix in suffixes:
                if word_to_add.endswith(suffix):
                    word_to_add = word_to_add[:-len(suffix)]
                    break
        
        # [최종 필터] 
        # 1. 글자수 2글자 이상
        # 2. 불용어(garbage)에 없어야 함
        # 3. 영어인 경우 소문자로 바꿔서 불용어 체크
        if len(word_to_add) >= 2 and word_to_add.lower() not in garbage:
            cleaned_words.append(word_to_add)
            
    return cleaned_words

def get_real_youtube_data():
    all_words = []
    
    if not API_KEY:
        return []

    print("🚀 프리미엄 데이터 수집 중...")
    
    for keyword in SEARCH_KEYWORDS:
        # viewCount(조회수) 순으로 가져와서 검증된 곳 위주로
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
        # 클릭시 '솔직후기' 검색
        search_query = f"부산 {word} 솔직후기" 
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
            
            /* SVG 반응형 설정 */
            svg { width: 95%; height: auto; max-width: 1200px; display: block; }
        </style>
    </head>
    <body>
        <div id="container">
            <h2>🌊 부산 핫플레이스 & 맛집</h2>
            <p class="footer">Premium YouTube Analysis • Updated: __DATE_PLACEHOLDER__</p>
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
                  .text(function(d) { return d.text + " (Click for Premium Info)"; });
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
