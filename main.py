import json
import re
import time
import base64
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import List
from datetime import datetime

@dataclass
class NoticeItem:
    id: str
    title: str
    writer: str
    date: str
    link: str
    category: str = "일반"
    is_pinned: bool = False
    site_name: str = "전자공학부"
    site_code: str = "knu_see"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 1. 전자공학부 수집 함수
def fetch_electronic_notices(max_pages: int = 3) -> List[NoticeItem]:
    all_notices = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        url = f"https://see.knu.ac.kr/content/board/notice.html?gtid=notice&page={page}"
        print(f"  └ [전자공학부] {page}/{max_pages} 페이지 요청 중...")
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.encoding = 'utf-8'
            if res.status_code != 200:
                continue
        except Exception as e:
            print(f"    └ 요청 에러: {e}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.select("table tbody tr")
        
        for row in rows:
            try:
                is_pinned = row.select_one("span.notice") is not None
                title_tag = row.select_one("td a")
                if not title_tag:
                    continue
                    
                raw_title = title_tag.text.strip()
                href = title_tag.get("href", "")
                
                fidx_match = re.search(r"fidx=(\d+)", href)
                if fidx_match:
                    fidx = fidx_match.group(1)
                    link = f"https://see.knu.ac.kr/content/board/notice.html?pg=vv&fidx={fidx}&gtid=notice&opt=&sword=&page=1&f_opt_1="
                else:
                    fidx = str(hash(raw_title))[:8]
                    link = "https://see.knu.ac.kr/content/board/" + href

                category = "일반"
                clean_title = raw_title
                category_match = re.search(r"^\[(.*?)\]", raw_title)
                if category_match:
                    category = category_match.group(1).strip()
                    clean_title = re.sub(r"^\[.*?\]\s*", "", raw_title).strip()

                cols = row.select("td")
                date = ""
                for col in cols:
                    text = col.text.strip()
                    if "-" in text or "." in text:
                        clean_text = text.replace(".", "-")
                        parts = clean_text.split("-")
                        if len(parts) == 3 and all(p.isdigit() for p in parts):
                            date = clean_text
                            break
                if not date:
                    date = datetime.now().strftime("%Y-%m-%d")

                if fidx in seen_ids:
                    continue
                seen_ids.add(fidx)

                all_notices.append(NoticeItem(
                    id=f"see_{fidx}",
                    title=clean_title,
                    writer="전자공학부",
                    date=date,
                    link=link,
                    category=category,
                    is_pinned=is_pinned,
                    site_name="전자공학부",
                    site_code="knu_see"
                ))
            except Exception:
                continue
        time.sleep(1)

    return all_notices

# 2. 자원봉사센터 수집 함수
def fetch_volunteer_notices(max_pages: int = 3) -> List[NoticeItem]:
    all_notices = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        start_page = (page - 1) * 10
        url = f"https://home.knu.ac.kr/HOME/volunteer/sub.htm?nav_code=vol1623744108&startPage={start_page}"
        print(f"  └ [자원봉사센터] {page}/{max_pages} 페이지 요청 중: {url}")
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.encoding = 'utf-8'
            if res.status_code != 200:
                print(f"    └ 응답 상태 코드 이상: {res.status_code}")
                continue
        except Exception as e:
            print(f"    └ 요청 에러: {e}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.select("table tbody tr") or soup.select("table tr")[1:]
        
        for row in rows:
            try:
                tds = row.find_all("td")
                if len(tds) < 5:
                    continue

                # 첫 번째 컬럼이 '공지'이면 상단 고정글
                num_text = tds[0].text.strip()
                is_pinned = (num_text == "공지")

                # 제목 링크 태그 탐색
                title_a = tds[1].find("a")
                if not title_a:
                    continue

                raw_title = title_a.text.strip()
                if not raw_title or len(raw_title) < 2:
                    continue

                href = title_a.get("href", "")

                # base64 인코딩된 mv_data에서 고유 idx 추출
                article_id = None
                try:
                    qs = parse_qs(urlparse(href).query)
                    mv_b64 = qs.get("mv_data", [""])[0].split("||")[0]
                    if mv_b64:
                        decoded = base64.b64decode(mv_b64).decode("utf-8", errors="ignore")
                        sub_qs = parse_qs(decoded)
                        article_id = sub_qs.get("idx", [None])[0]
                except Exception:
                    pass

                if not article_id:
                    article_id = str(hash(raw_title))[:8]

                # 절대경로 URL 완성
                if href.startswith("http"):
                    link = href
                elif href.startswith("/"):
                    link = "https://home.knu.ac.kr" + href
                else:
                    link = "https://home.knu.ac.kr/HOME/volunteer/" + href

                # 카테고리 파싱 (예: [마감], [추가모집] 등 또는 기본 '봉사')
                category = "봉사"
                clean_title = raw_title
                category_match = re.search(r"^\[(.*?)\]", raw_title)
                if category_match:
                    category = category_match.group(1).strip()
                    clean_title = re.sub(r"^\[.*?\]\s*", "", raw_title).strip()

                # 작성자 및 작성일 파싱
                writer = tds[3].text.strip() if len(tds) > 3 and tds[3].text.strip() else "자원봉사센터"
                
                date = ""
                raw_date = tds[4].text.strip() if len(tds) > 4 else ""
                if "-" in raw_date or "." in raw_date:
                    clean_date = raw_date.replace(".", "-")
                    parts = clean_date.split("-")
                    if len(parts) == 3 and all(p.isdigit() for p in parts):
                        date = clean_date
                if not date:
                    date = datetime.now().strftime("%Y-%m-%d")

                if article_id in seen_ids:
                    continue
                seen_ids.add(article_id)

                all_notices.append(NoticeItem(
                    id=f"vol_{article_id}",
                    title=clean_title,
                    writer=writer,
                    date=date,
                    link=link,
                    category=category,
                    is_pinned=is_pinned,
                    site_name="자원봉사센터",
                    site_code="knu_vol"
                ))
            except Exception:
                continue

        time.sleep(1)

    return all_notices

def main():
    print("=== 경북대학교 통합 공지사항 수집 시작 ===")
    
    print("\n1. 전자공학부 수집 시작")
    see_data = fetch_electronic_notices(max_pages=3)
    print(f"  └ [결과] 전자공학부 공지사항: {len(see_data)}개 수집 완료")
    
    print("\n2. 자원봉사센터 수집 시작")
    vol_data = fetch_volunteer_notices(max_pages=3)
    print(f"  └ [결과] 자원봉사센터 공지사항: {len(vol_data)}개 수집 완료")
    
    total_data = see_data + vol_data
    
    if not total_data:
        print("\n수집된 데이터가 없습니다.")
        return

    notice_list = [asdict(item) for item in total_data]
    
    with open("notices.json", "w", encoding="utf-8") as f:
        json.dump(notice_list, f, ensure_ascii=False, indent=2)
    
    print(f"\n==========================================")
    print(f"수집 요약:")
    print(f"  - 전자공학부: {len(see_data)}개")
    print(f"  - 자원봉사센터: {len(vol_data)}개")
    print(f"  - 총합: {len(total_data)}개 -> notices.json 저장 완료")
    print(f"==========================================")

if __name__ == "__main__":
    main()