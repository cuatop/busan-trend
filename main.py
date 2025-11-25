import requests
import json
import datetime
import re
import os
from collections import Counter
import urllib.parse
import time # 1초 쉬어가기를 위해 필요

# === 설정 ===
API_KEY = os.environ.get('YOUTUBE_API_KEY')
MAX_RESULTS = 40 

# === [핵심 수정] 구별 스마트 검색어 매핑 ===
# 행정구역 이름만 쓰지 않고, 실제 사람들이 많이 쓰는 '핫플 지명'을 추가했습니다.
DISTRICT_KEYWORDS = {
    "부산 전체": ["부산 맛집", "부산 여행", "부산 핫플", "부산 가볼만한곳"],
    "해운대구": ["해운대 맛집", "해리단길", "센텀시티 맛집", "달맞이길 카페"],
    "수영구": ["광안리 맛집", "광안리 카페", "민락더마켓", "남천동 빵집"], # 수영구 -> 광안리
    "기장군": ["기장 맛집", "기장 카페", "부산 롯데월드 맛집", "연화리 해녀촌"],
    "영도구": ["부산 영도 맛집", "흰여울문화마을 카페", "영도 포장마차"],
    "부산진구": ["서면 맛집", "전포동 카페거리", "전포 핫플", "부산 시민공원 맛집"],
    "동래구": ["동래 맛집", "온천천 카페거리", "동래파전", "부산대 맛집"],
    "금정구": ["부산대 맛집", "범어사 맛집", "부산대 카페"],
    "남구": ["경성대 부경대 맛집", "부산 용호동 맛집", "이기대 맛집"],
    "중구": ["남포동 맛집", "자갈치시장 맛집", "부산 깡통시장", "보수동 책방골목"], # 중구 -> 남포동
    "서구": ["부산 송도 맛집", "송도해수욕장 카페", "부산 대신동 맛집"],
    "동구": ["부산역 맛집", "초량 이바구길", "초량 불백", "부산 차이나타운"],
    "사하구": ["다대포 맛집", "하단 맛집", "감천문화마을 맛집"],
    "사상구": ["사상 맛집", "사상 핫플", "괘법동 맛집"],
    "북구": ["덕천 맛집", "화명동 맛집", "부산 구포시장"],
    "강서구": ["명지 맛집", "명지국제신도시", "가덕도 맛집", "부산 강서구 카페"],
    "연제구": ["연산동 맛집", "부산 시청 맛집", "연산동 술집"]
}

# === [비상용] 데이터가 0개일 때 보여줄 기본 키워드 (절대 빈 화면 안 뜨게 함) ===
BACKUP_DATA = {
    "수영구": [("광안리해수욕장", 50), ("민락수변공원", 40), ("드론쇼", 30), ("톤쇼우", 25)],
    "기장군": [("해동용궁사", 50), ("아난티코브", 40), ("칠드런스뮤지엄", 30), ("롯데아울렛", 25)],
    "영도구": [("흰여울문화마을", 50), ("피아크", 40), ("태종대", 30), ("해녀촌", 25)],
    "중구": [("BIFF광장", 50), ("국제시장", 40), ("용두산공원", 30), ("씨앗호떡", 25)],
    "서구": [("송도케이블카", 50), ("암남공원", 40), ("조개구이", 30), ("고등어축제", 25)],
    "연제구": [("온천천", 50), ("연산로터리", 40), ("고분군", 30), ("배산", 25)]
}

def clean_korean_text(text):
    # 특수문자 및 잡다한 용어 제거
    text = re.sub(r'[a-zA-Z0-9]', ' ', text)
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    words = text.split()
    cleaned_words = []
    
    garbage = set([
        "부산", "맛집", "여행", "브이로그", "먹방", "영상", "구독", "좋아요", "알람",
        "추천", "강추", "방문", "후기", "리뷰", "소개", "총정리", "모음", "코스",
        "진짜", "정말", "완전", "대박", "역대급", "최고", "유명한", "솔직", "숨은", 
        "가성비", "존맛", "꿀맛", "무조건", "절대", "실패", "없는", "성공", "인생",
        "오늘", "내일", "시간", "위치", "가격", "주차", "예약", "웨이팅", "정보",
        "가는", "오는", "먹는", "보는", "하는", "있는", "가본", "먹어본", "가세요",
        "사람", "현지인", "토박이", "외국인", "커플", "데이트", "핫플", "꿀팁",
        "댓글", "선정", "가봐야", "추천하", "토박이들", "나혼자", "혼자", "가봤습니다", 
        "베스트", "가이드", "유명한곳", "년", "월", "일", "질문", "답변", "반응"
    ])
    
    for w in words:
        word_to_add = w
        if len(word_to_add) > 1:
            for suffix in ["은", "는", "이", "가", "을", "를", "에", "의", "서", "로", "와", "과", "도", "만", "에서", "이랑", "까지", "부터", "네요", "세요", "입니다"]:
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
            # [중요] 구글 API에 너무 빨리 요청하면 차단되므로 0.5초 쉼
            time.sleep(0.5)
        except: continue
    return Counter(all_words).most_common(50)

# === 메인 로직 실행 ===
print("🚀 지역별 데이터 수집 시작...")
final_json = {}

for region, keywords in DISTRICT_KEYWORDS.items():
    print(f"-> {region} 수집 중 ({keywords})")
    data = fetch_youtube_data(keywords)
    
    # [안전장치] 만약 데이터가 없으면 백업 데이터 사용
    if not data and region in BACKUP_DATA:
        print(f"  ⚠️ {region} 데이터 없음 -> 비상용 데이터 사용")
        data = BACKUP_DATA[region]
        
    # D3 포맷 변환
    d3_list = []
    if data:
        max_count = data[0][1]
        for word, count in data:
            # 클릭 시 검색어: "부산 [지역명] [키워드]"
            search_query = f"{keywords[0]} {word}"
            link = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
            size = 15 + (count / max_count) * 90
            d3_list.append({"text": word, "size": size, "url": link, "count": count})
    
    # 딕셔너리 키를 영어(Busan, Haeundae...)가 아닌 한글(부산 전체, 해운대구...)로 저장
    final_json[region] = d3_list

# === HTML 생성 ===
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
        body { margin: 0; padding: 0; background-color: #e0f7fa; font-family: 'Noto Sans KR', sans-serif; overflow: auto; text-align: center;}
        #container { width: 100%; min-height: 100vh; padding-top: 20px; display: flex; flex-direction: column; align-items: center; }
        
        /* 버튼 디자인 개선 */
        #planet-system {
            width: 95%; max-width: 900px;
            display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;
            margin-bottom: 20px;
        }
        .btn {
            border: none; padding: 8px 16px; border-radius: 25px;
            font-family: 'Noto Sans KR', sans-serif; font-weight: 700; cursor: pointer;
            transition: all 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            font-size: 14px; background: white; color: #006064;
        }
        .btn:hover { transform: translateY(-2px); background: #b2ebf2; }
        .btn.active { background: #006064; color: white; box-shadow: 0 4px 10px rgba(0,96,100,0.4); transform: scale(1.05); }
        .btn-busan { background: #00498c; color: white; font-size: 16px; padding: 10px 20px; }

        #cloud-area { width: 95%; height: 600px; margin-top: 10px; }
        h2 { color: #006064; margin: 0 0 10px 0; font-family: 'Black Han Sans'; font-size: 2.2em; text-shadow: 2px 2px 0px white; }
        .current-title { color: #d84315; }
        .word-link { cursor: pointer; transition: all 0.2s ease; }
        .word-link:hover { opacity: 0.7 !important; text-shadow: 1px 1px 5px rgba(255,255,255,0.8); }
        svg { width: 100%; height: 100%; display: block; }
    </style>
</head>
<body>
    <div id="container">
        <h2>🌊 <span id="region-title" class="current-title">부산 전체</span> 핫플 지도</h2>
        <p style="font-size: 12px; color: #666; margin-bottom: 20px;">Updated: __DATE_PLACEHOLDER__</p>

        <div id="planet-system">
            <button class="btn btn-busan active" onclick="changeRegion('부산 전체')">부산 전체</button>
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

        drawCloud(allData['부산 전체']);

        function changeRegion(region) {
            document.getElementById('region-title').innerText = region;
            
            var btns = document.getElementsByClassName('btn');
            for (var i = 0; i < btns.length; i++) {
                btns[i].classList.remove('active');
                if (btns[i].innerText === region) {
                    btns[i].classList.add('active');
                }
            }

            document.getElementById('cloud-area').innerHTML = '';
            
            if (allData[region] && allData[region].length > 0) {
                drawCloud(allData[region]);
            } else {
                // 데이터가 아예 없을 때(비상 데이터도 실패 시) 처리
                document.getElementById('cloud-area').innerHTML = '<h3 style="color:#666; margin-top:50px;">데이터를 수집 중입니다...</h3>';
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
        
        window.addEventListener('resize', function() {
            var currentRegion = document.getElementById('region-title').innerText;
            document.getElementById('cloud-area').innerHTML = '';
            if(allData[currentRegion]) drawCloud(allData[currentRegion]);
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
