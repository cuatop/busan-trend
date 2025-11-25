import requests
import json
import datetime
import re
import os
from collections import Counter
import urllib.parse

# === 설정 ===
API_KEY = os.environ.get('YOUTUBE_API_KEY')
MAX_RESULTS = 30 # 각 구별 검색량 (API 한도 절약 위해 조절)

# 부산 전체 검색어
BUSAN_KEYWORDS = ["부산 현지인 맛집", "부산 핫플", "부산 여행 코스", "부산 축제", "부산 미쉐린"]

# 16개 구/군 리스트
DISTRICTS = [
    "강서구", "금정구", "남구", "동구", "동래구", "부산진구", "북구", 
    "사상구", "사하구", "서구", "수영구", "연제구", "영도구", "중구", "해운대구", "기장군"
]

def clean_korean_text(text):
    # 프리미엄 필터링 (잡다한 단어 제거)
    text = re.sub(r'[a-zA-Z0-9]', ' ', text)
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    words = text.split()
    cleaned_words = []
    
    garbage = set([
        "부산", "맛집", "여행", "브이로그", "먹방", "영상", "구독", "좋아요", "알람", "설정",
        "추천", "강추", "방문", "후기", "리뷰", "소개", "비교", "분석", "총정리", "모음",
        "진짜", "정말", "완전", "대박", "역대급", "최고", "유명한", "솔직", "숨은", "나만",
        "가성비", "존맛", "꿀맛", "무조건", "절대", "실패", "없는", "성공", "인생",
        "오늘", "내일", "주말", "평일", "시간", "위치", "가격", "주차", "예약", "웨이팅",
        "가는", "오는", "먹는", "보는", "하는", "있는", "가본", "먹어본", "가세요", "오세요",
        "사람", "현지인", "토박이", "외국인", "커플", "가족", "데이트", "코스", "핫플", "정보", "꿀팁",
        "댓글", "선정", "가봐야", "추천하", "토박이들", "나혼자", "혼자", "가봤습니다", "모음집",
        "베스트", "가이드", "유명한곳", "연속", "년", "월", "일", "질문", "답변", "반응"
    ])
    
    suffixes = ["은", "는", "이", "가", "을", "를", "에", "의", "서", "로", "와", "과", "도", "만", "이나", "에서", "이랑", "까지", "부터", "네요", "세요", "인가", "입니다"]

    for w in words:
        word_to_add = w
        if len(word_to_add) > 1:
            for suffix in suffixes:
                if word_to_add.endswith(suffix):
                    word_to_add = word_to_add[:-len(suffix)]
                    break
        if len(word_to_add) >= 2 and word_to_add not in garbage:
            cleaned_words.append(word_to_add)
    return cleaned_words

def fetch_youtube_data(keywords):
    all_words = []
    if not API_KEY: return []
    
    for keyword in keywords:
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
    return Counter(all_words).most_common(60)

# === 1. 부산 전체 데이터 수집 ===
print("🚀 부산 전체 데이터 수집 중...")
busan_data = fetch_youtube_data(BUSAN_KEYWORDS)

# === 2. 구/군별 데이터 수집 ===
district_data_map = {}
for dist in DISTRICTS:
    print(f"🚀 {dist} 데이터 수집 중...")
    # 검색어 예: "부산 동래구 맛집", "부산 동래구 핫플"
    keywords = [f"부산 {dist} 맛집", f"부산 {dist} 가볼만한곳"]
    data = fetch_youtube_data(keywords)
    district_data_map[dist] = data

# === 데이터 포장 (D3용 포맷) ===
def format_for_d3(counter_data, region_name):
    d3_list = []
    if not counter_data: return []
    max_count = counter_data[0][1]
    for word, count in counter_data:
        search_query = f"부산 {region_name} {word} 후기"
        link = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
        size = 15 + (count / max_count) * 90
        d3_list.append({"text": word, "size": size, "url": link, "count": count})
    return d3_list

final_json = {
    "Busan": format_for_d3(busan_data, ""),
}
for dist, data in district_data_map.items():
    final_json[dist] = format_for_d3(data, dist)

# === HTML 생성 (인터랙티브 UI) ===
html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Busan Interactive Map</title>
    <script src="https://d3js.org/d3.v5.min.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/holtzy/D3-graph-gallery@master/LIB/d3.layout.cloud.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; background-color: #e0f7fa; font-family: 'Noto Sans KR', sans-serif; overflow-x: hidden; }
        
        /* 상단 네비게이션 (모바일용 & 보조) */
        #nav-bar { padding: 10px; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; display: none; }
        
        /* 메인 컨테이너 */
        #container { display: flex; flex-direction: column; align-items: center; min-height: 100vh; padding-top: 20px; }
        
        /* 1. 구/군 선택 버튼 영역 (행성계 모양) */
        #planet-system {
            position: relative;
            width: 100%;
            max-width: 800px;
            height: 200px; /* 모바일에서는 줄임 */
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 8px;
        }

        /* 버튼 스타일 */
        .btn {
            border: none; padding: 8px 15px; border-radius: 20px;
            font-family: 'Noto Sans KR', sans-serif; font-weight: bold; cursor: pointer;
            transition: all 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            font-size: 14px; background: white; color: #006064;
        }
        .btn:hover { transform: scale(1.1); background: #b2ebf2; }
        .btn.active { background: #006064; color: white; box-shadow: 0 0 10px #00bcd4; transform: scale(1.1); }
        
        /* 중앙 '부산' 버튼 (특별 대우) */
        .btn-busan {
            background: #00498c; color: white; font-size: 18px; padding: 10px 25px; border: 2px solid white;
        }

        /* 2. 워드클라우드 영역 */
        #cloud-area { width: 95%; height: 600px; position: relative; }
        svg { width: 100%; height: 100%; display: block; }
        
        h2 { color: #006064; margin: 0; font-family: 'Black Han Sans'; font-size: 2em; text-shadow: 2px 2px 0px white; }
        .current-title { color: #d84315; }
        .word-link { cursor: pointer; transition: all 0.2s ease; }
        .word-link:hover { opacity: 0.7 !important; }

        /* PC 화면에서 행성계 모양 만들기 */
        @media (min-width: 768px) {
            #planet-system { height: auto; margin-bottom: 30px; }
            .btn { margin: 5px; }
        }
    </style>
</head>
<body>
    <div id="container">
        <h2>🌊 <span id="region-title" class="current-title">부산 전체</span> 핫플 지도</h2>
        <p style="font-size: 12px; color: #666; margin-bottom: 20px;">Updated: __DATE_PLACEHOLDER__</p>

        <div id="planet-system">
            <button class="btn btn-busan active" onclick="changeRegion('Busan')">부산 전체</button>
            <button class="btn" onclick="changeRegion('해운대구')">해운대구</button>
            <button class="btn" onclick="changeRegion('수영구')">수영구</button>
            <button class="btn" onclick="changeRegion('기장군')">기장군</button>
            <button class="btn" onclick="changeRegion('영도구')">영도구</button>
            <button class="btn" onclick="changeRegion('부산진구')">부산진구</button>
            <button class="btn" onclick="changeRegion('동래구')">동래구</button>
            <button class="btn" onclick="changeRegion('금정구')">금정구</button>
            <button class="btn" onclick="changeRegion('남구')">남구</button>
            <button class="btn" onclick="changeRegion('중구')">중구</button>
            <button class="btn" onclick="changeRegion('서구')">서구</button>
            <button class="btn" onclick="changeRegion('동구')">동구</button>
            <button class="btn" onclick="changeRegion('사하구')">사하구</button>
            <button class="btn" onclick="changeRegion('사상구')">사상구</button>
            <button class="btn" onclick="changeRegion('북구')">북구</button>
            <button class="btn" onclick="changeRegion('강서구')">강서구</button>
            <button class="btn" onclick="changeRegion('연제구')">연제구</button>
        </div>

        <div id="cloud-area"></div>
    </div>

    <script>
        var allData = __DATA_PLACEHOLDER__;
        var myColor = d3.scaleOrdinal().range(["#01579b", "#0288d1", "#00acc1", "#00bfa5", "#ff6f00", "#d84315", "#c2185b"]);
        var layout;

        // 초기 실행 (부산 전체)
        drawCloud(allData['Busan']);

        function changeRegion(region) {
            // 1. 제목 변경
            document.getElementById('region-title').innerText = (region === 'Busan') ? '부산 전체' : region;
            
            // 2. 버튼 활성화 스타일 변경
            var btns = document.getElementsByClassName('btn');
            for (var i = 0; i < btns.length; i++) {
                btns[i].classList.remove('active');
                if (btns[i].innerText.includes(region === 'Busan' ? '부산' : region)) {
                    btns[i].classList.add('active');
                }
            }

            // 3. 구름 다시 그리기
            document.getElementById('cloud-area').innerHTML = ''; // 기존 그림 지우기
            if (allData[region] && allData[region].length > 0) {
                drawCloud(allData[region]);
            } else {
                document.getElementById('cloud-area').innerHTML = '<h3>데이터가 없습니다.</h3>';
            }
        }

        function drawCloud(words) {
            var width = document.getElementById('cloud-area').offsetWidth;
            var height = 600;

            layout = d3.layout.cloud()
                .size([width, height])
                .words(words.map(function(d) { return {text: d.text, size: d.size, url: d.url, count: d.count}; }))
                .padding(5)
                .rotate(function() { return (~~(Math.random() * 6) - 3) * 30; })
                .font("Noto Sans KR")
                .fontWeight("900")
                .fontSize(function(d) { return d.size; })
                .on("end", draw);

            layout.start();
        }

        function draw(words) {
            var width = layout.size()[0];
            var height = layout.size()[1];

            d3.select("#cloud-area").append("svg")
                .attr("viewBox", "0 0 " + width + " " + height)
                .attr("preserveAspectRatio", "xMidYMid meet")
                .append("g")
                .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")")
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
                .text(function(d) { return d.text; });
        }
        
        // 화면 크기 바뀔 때 재조정
        window.addEventListener('resize', function() {
            var currentRegion = document.querySelector('.btn.active').innerText.replace(' 전체', '');
            if(currentRegion === '부산') currentRegion = 'Busan';
            
            document.getElementById('cloud-area').innerHTML = '';
            drawCloud(allData[currentRegion]);
        });
    </script>
</body>
</html>
"""

json_str = json.dumps(final_json)
today_str = datetime.date.today().strftime('%Y-%m-%d')
final_html = html_template.replace("__DATA_PLACEHOLDER__", json_str).replace("__DATE_PLACEHOLDER__", today_str)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_html)
print("성공! 인터랙티브 부산 지도 생성 완료")
