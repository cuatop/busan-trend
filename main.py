import requests
import json
import datetime
import re
import os
from collections import Counter
import urllib.parse

# === 설정 ===
SEARCH_KEYWORDS = [
    "부산 현지인 맛집", "부산 미쉐린 가이드", "부산 블루리본 맛집", 
    "부산 기장 찐맛집", "부산 영도 흰여울길 맛집", "부산 광안리 오션뷰 카페", 
    "부산 해운대 암소갈비", "부산 전포동 카페거리", "부산 깡통시장 먹거리",
    "부산 노포 맛집", "부산 돼지국밥 로컬", "부산 밀면 3대"
]
MAX_RESULTS = 50

API_KEY = os.environ.get('YOUTUBE_API_KEY')

def clean_korean_text(text):
    # 1. 영어, 숫자, 특수문자 삭제
    text = re.sub(r'[a-zA-Z0-9]', ' ', text)
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    
    words = text.split()
    cleaned_words = []
    
    # 2. [독한 필터] 선생님이 지적하신 단어 + 잡다한 단어 블랙리스트
    garbage = set([
        # 지적하신 단어들
        "댓글", "선정", "선정된", "가봐야", "가볼만한", "추천하", "추천한", "추천해", 
        "추천하는", "토박이들", "현지인들", "나혼자", "혼자", "가봤습니다", 
        # 지역/광범위 명사
        "부산", "한국", "경남", "전국", "지역", "동네", "국내", "경상도",
        # 유튜브 상투어
        "맛집", "여행", "관광", "투어", "후기", "리뷰", "브이로그", "먹방", "영상", 
        "채널", "구독", "좋아요", "알람", "설정", "공개", "특집", "모음", "모음집",
        "총정리", "비교", "분석", "소개", "추천", "강추", "방문", "탐방", "도전",
        "가이드", "베스트", "best", "top", "로그", "브이", 
        # 무의미한 수식어/형용사
        "진짜", "정말", "완전", "대박", "역대급", "최고", "유명한", "솔직", "숨은", 
        "나만", "알고싶은", "비밀", "가성비", "저렴한", "비싼", "존맛", "꿀맛", 
        "미친", "개쩌는", "무조건", "절대", "실패", "없는", "성공", "인생", "찐맛집",
        "유명한곳", "갈만한곳", "가볼만한곳", "핫플", "핫플레이스",
        # 시간/단위/기타
        "오늘", "지금", "어제", "내일", "주말", "평일", "시간", "위치", "가격", 
        "주차", "예약", "웨이팅", "여기", "저기", "거기", "어디", "곳은", "곳이", 
        "가장", "제일", "바로", "역시", "혹시", "무려", "특히", "연속", "년", "월", "일",
        "사람", "현지인", "토박이", "외국인", "커플", "가족", "친구", "남자", "여자",
        "데이트", "코스", "여행지", "명소", "정보", "꿀팁", "이유", "충격", "실화",
        "질문", "답변", "반응", "모음", "근황", "일상", "따라", "따라하기"
    ])
    
    # 동사/형용사 어미 처리 (가봤 -> 가다, 먹는 -> 먹다 등 방지 위해 아예 삭제)
    verb_endings = ["다", "요", "죠", "네", "가", "나", "는", "은", "를", "을", "에", "서", "로", "와", "과", "고", "며", "면", "지", "듯", "게"]

    for w in words:
        word_to_add = w
        
        # 1차 필터: 조사 제거
        if len(word_to_add) > 1:
            for suffix in ["은", "는", "이", "가", "을", "를", "에", "의", "서", "로", "와", "과", "도", "만", "한테", "에서", "이랑", "까지"]:
                if word_to_add.endswith(suffix):
                    word_to_add = word_to_add[:-len(suffix)]
                    break
        
        # 2차 필터: 동사/형용사 활용형 강력 차단
        # "추천하" 같은게 남지 않도록, 끝이 이상하게 끝나는 말 제외
        # (명사는 보통 받침이 있거나 깔끔하게 떨어짐)
        is_verb_form = False
        if word_to_add.endswith("하") or word_to_add.endswith("해") or word_to_add.endswith("한") or word_to_add.endswith("된") or word_to_add.endswith("된") or word_to_add.endswith("할") or word_to_add.endswith("될"):
             is_verb_form = True

        # [최종 합격 기준]
        # 1. 2글자 이상
        # 2. 블랙리스트(garbage)에 없어야 함
        # 3. 동사 활용형 찌꺼기가 아니어야 함
        if len(word_to_add) >= 2 and word_to_add not in garbage and not is_verb_form:
            cleaned_words.append(word_to_add)
            
    return cleaned_words

def get_real_youtube_data():
    all_words = []
    
    if not API_KEY:
        return []

    print("🚀 최고급 데이터 정제 중...")
    
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
            
    # 상위 60개만 아주 엄선 (개수를 줄여서 퀄리티 높임)
    return Counter(all_words).most_common(60)

try:
    word_counts = get_real_youtube_data()
except:
    word_counts = []

d3_data = []
if word_counts:
    max_count = word_counts[0][1]
    for word, count in word_counts:
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
