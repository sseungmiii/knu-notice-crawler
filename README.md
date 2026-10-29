# 경북대학교 공지 수집기

전자공학부와 자원봉사센터의 공개 공지를 수집하는 Python 프로그램과 정적 대시보드입니다. 기존 로컬 프로젝트 `knu-notices`의 코드·데이터를 내용 변경 없이 가져왔습니다.

## 구성

- `main.py`: requests/BeautifulSoup 수집기. 직접 실행하면 현재 작업 폴더의 `notices.json`을 갱신합니다.
- `notices.json`: 수집 결과. 가져온 파일에는 공지 122건이 있으며 최신 수집 완료를 의미하지 않습니다.
- `index.html`: 같은 폴더의 `./notices.json`을 읽는 화면.
- `requirements.txt`: 실행에 필요한 Python 라이브러리.

## 개발

Python 3.11 이상에서 저장소 루트를 작업 폴더로 사용합니다.

```sh
python -m venv .venv
# 환경에 맞게 .venv를 활성화한 뒤
python -m pip install -r requirements.txt
python -c "import ast,pathlib; ast.parse(pathlib.Path('main.py').read_text(encoding='utf-8')); import requests, bs4, main"
python -m json.tool notices.json > /dev/null
```

Windows PowerShell에서 JSON 출력만 숨기려면 마지막 명령의 `/dev/null` 대신 `$null`을 사용합니다. Python 검사에는 필요 시 `-B`를 붙여 캐시 생성을 막을 수 있습니다. 별도 타입 검사·프런트엔드 빌드·자동 테스트 도구는 아직 없습니다.

## 화면 확인과 실제 수집

화면만 확인할 때는 임시 공개 폴더에 `index.html`, `notices.json`만 복사해 정적 서버로 제공합니다. 저장소 전체를 공개 서버 루트로 노출하지 않습니다. 예를 들어 두 파일을 복사한 폴더에서 `python -m http.server 8080 --bind 127.0.0.1`을 실행합니다.

실제 갱신이 필요할 때만 저장소 루트에서 `python main.py`를 실행합니다. 현재 코드는 CWD 기준 저장 경로를 사용하고 일부 수집만 성공해도 결과를 쓸 수 있으므로, 기존 JSON 보존과 diff 검토가 필요합니다. 기존 동작을 이번 환경 준비에서 변경하지 않았습니다.

현재 저장소에는 GitHub Actions 자동 수집이나 Vercel 배포 설정이 없습니다. 코드 업로드·클라우드 개발 환경 생성과 운영 서비스 배포를 구분합니다. 외부 게시판 요청은 사이트 접근 가능 여부와 구조 변경의 영향을 받으며 이번 코드 반영에서 실제 수집은 실행하지 않았습니다.

## 클라우드 작업

이 저장소 하나만 선택한 개인용 환경을 사용합니다. Python 의존성 설치 후 문법·라이브러리 import·JSON 구조·정적 HTTP 응답을 확인합니다. 실제 수집·데이터 갱신·운영 배포는 별도 작업 범위로 요청합니다. 비밀 키는 현재 코드의 필수 설정이 아니며 계정·비밀번호를 요청하거나 기록하지 않습니다.
