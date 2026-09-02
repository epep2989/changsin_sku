# 창신리빙 입점현황 조회 웹사이트

이 폴더 안 파일들을 GitHub → Render에 올리면, 팀원 누구나 인터넷 주소로 들어가서
품목코드/상품명을 검색해 어느 채널에 팔리고 있는지 확인할 수 있는 웹사이트가 만들어집니다.

설치 방법은 아주 쉬운 그림/단계별 설명으로 별도 가이드 페이지에 정리해뒀습니다 (대화에서 링크로 전달드렸어요).

## 폴더 구성
- `app.py` — 화면(로그인 페이지, 검색 페이지)
- `channel_search.py` — 실제로 각 채널에 검색을 보내는 로직
- `platforms/` — 채널별(쿠팡/네이버/11번가/카페24 등) 연동 코드
- `requirements.txt` — 필요한 파이썬 패키지 목록
- `render.yaml` — Render에 올릴 때 자동으로 설정을 읽어가는 파일 (건드릴 필요 없음)

## 로컬에서 직접 테스트하고 싶다면 (선택사항, 몰라도 됨)
```bash
pip install -r requirements.txt
SITE_PASSWORD=아무비번 FLASK_SECRET_KEY=아무값 python3 app.py
```
그 다음 브라우저에서 http://localhost:5000 접속.
