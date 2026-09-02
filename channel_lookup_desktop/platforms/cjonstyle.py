"""
CJ온스타일 연동 모듈 - 뼈대만 제공

확인된 사실:
- CJ온스타일 파트너시스템(https://partners.cjonstyle.com) 안에 "표준 API"가 공식 제공됩니다.
- 파트너시스템 > API 관리 > API 정보관리 메뉴에서 기본정보 등록 후 API 인증키 발급.
- 호출 IP를 등록해야 방화벽이 허용되며, 영업일 기준 2~3일이 걸립니다.
- REST 방식, JSON 형식, GET(조회)/POST(생성) 지원.

이번 조사로 확인 못한 것: 정확한 엔드포인트 경로, 인증 헤더 이름, 상품 조회 API의
요청/응답 필드명 (API Docs 페이지가 로그인 후에만 상세 내용을 보여주는 구조였습니다).

API 신청/문서: https://partners.cjonstyle.com/standardApi (입점 협력사 계정 필요)
"""
from __future__ import annotations

from ._gated_scaffold import not_yet_implemented


class CjOnstyleClient:
    def __init__(self, api_key: str | None = None, vendor_id: str | None = None, **kwargs):
        self.api_key = api_key
        self.vendor_id = vendor_id

    def search_products(self, keyword: str | None = None) -> list[dict]:
        not_yet_implemented("CJ온스타일", "https://partners.cjonstyle.com/standardApi")
