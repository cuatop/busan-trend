import requests
import json
import datetime
import re
import os
from collections import Counter
import urllib.parse

# === 설정 ===
# 검색의 '씨앗'이 되는 단어들입니다. (이 단어들로 검색해서 나온 '결과'를 분석합니다)
# 100개를 적을 필요 없이, 큰 주제만 던져주면 로봇이 알아서 세부 단어를 긁어옵니다.
SEED_KEYWORDS = ["부산 맛집", "부산 여행", "부산 핫플", "부산 카페", "해운대 맛집", "광안리 맛집", "기장 맛집", "전포동 카페", "Busan Food"]
MAX_RESULTS = 50 # 키워드당 가져올 영상 개수 (API 하루 한도 고려)

# === [핵심] 깃허브 금고에서 API 키 꺼내기 ===
API_KEY = os.environ.get('YOUTUBE_API_KEY')

def clean_korean_text(text):
    # 특수문자 제거
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    words = text.split()
    
    cleaned_words = []
    # 불용어 (워드클라우드에 안 나왔으면 하는 단어들)
    garbage = [
        "부산", "맛집", "여행", "브이로그", "Vlog", "Korea", "Busan", "Food", "Mukbang", "먹방", 
        "추천", "코스", "진짜", "정말", "하는", "있는", "가볼만한곳", "Best", "Top", "존맛", 
        "영상", "오늘", "투어", "후기", "식당", "카페", "Cafe", "Street", "Review", "리뷰",
        "2024", "2025", "1박2일", "2박3일", "사람", "이유", "충격", "공개", "가지", "모음",
        "현지인", "솔직", "방문", "위치", "가격", "메뉴", "대박", "유명한", "웨이팅", "필수",
        "총정리", "실패", "없는", "무조건", "Best5", "Best10", "내돈내산", "Eng", "Sub"
    ]
    
    for w in words:
        # 조사 제거 (간단 버전)
        if len(w) > 2:
            for josa in ["은", "는", "이", "가", "을", "를", "에", "의", "서", "로", "고", "하고", "에서"]:
                if w.endswith(josa):
                    w = w[:-len(josa)]
                    break
        
        if len(w) >= 2 and w not in garbage:
            cleaned_words.append(w)
            
    return cleaned_words

def get_real_youtube_data():
    all_words = []
    video_links = {} 
    
    if not API_KEY:
        print("🚨 오류: API 키가 없습니다! GitHub Secrets를 확인해주세요.")
        return [], {}

    print("🚀 유튜브 API로 실시간 데이터를 긁어옵니다...")
    
    for keyword in SEED_KEYWORDS:
        print(f"- 검색중: {keyword}")
        # 유튜브 정식 API 주소 (정문)
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={keyword}&key={API_KEY}&maxResults={MAX_RESULTS}&type=video&order=date"
        # order=date: 최신순, order=viewCount: 조회수순 (원하는대로 변경 가능)
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if 'items' in data:
                for item in data['items']:
                    title = item['snippet']['title']
                    video_id = item['id']['videoId']
                    
                    # 제목에서 단어 추출
                    words = clean_korean_text(title)
                    all_words.extend(words)
                    
                    # 단어 클릭시 이동할 영상 링크 저장
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    for w in words:
                        if w not in video_links: # 이미 있으면 놔두고, 없으면 등록
                            video_links[w] = video_url
            else:
                print(f"  -> 결과 없음 (혹은 할당량 초과): {data.get('error', {}).get('message')}")
                
        except Exception as e:
            print(f"  -> 접속 에러: {e}")
            continue
            
    # 가장 많이 나온 단어 80개 추출
    return Counter(all_words).most_common(80), video_links

# === 실행 ===
word_counts, links = get_real_youtube_data()

# === HTML 생성 (D3.js 꽉 찬 디자인) ===
d3_data = []
if word_counts:
    max_count = word_counts[0][1]
    for word, count in word_counts:
        # API에서 찾은 실제 영상 링크 연결
        link = links.get(word, "https://www.youtube.com/results?search_query=부산+" + word)
        size = 15 + (count / max_count) * 90
        d3_data.append({"text": word, "size": size, "url": link, "count": count})

    # HTML 작성 (반응형)
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
                background-color: #e0f7fa; 
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
            <p class="footer">Real-time YouTube Trend • Updated: {datetime.date.today().strftime('%Y-%m-%d')}</p>
            <div id="cloud-area"></div>
        </div>

        <script>
            var words = {json.dumps(d3_data)};
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
                  .attr("transform", "translate(" + layoutWidth / 2 + "," + layoutHeight / 2 + ")")
                .selectAll("text")
                  .data(words)
                .enter().append("text")
                  .attr("class", "word-link")
                  .style("font-size", function(d) {{ return d.size + "px"; }})
                  .style("font-family", "'Noto Sans KR', sans-serif")
                  .style("font-weight", "900")
                  .style("fill", function(d, i) {{ return myColor(i); }})
                  .attr("text-anchor", "middle")
                  .attr("transform", function(d) {{
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                  }})
                  .text(function(d) {{ return d.text; }})
                  .on("click", function(d) {{ window.open(d.url, '_blank'); }})
                  .append("title")
                  .text(function(d) {{ return d.text + " (YouTube)"; }});
            }}
        </script>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("성공! index.html 생성 완료")
else:
    print("데이터 수집 실패")
    # 에러 시 보여줄 화면
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<h2>데이터를 가져오지 못했습니다. API 키를 확인해주세요.</h2>")
