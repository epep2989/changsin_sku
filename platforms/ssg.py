"""
SSG(신세계/이마트, SSG.COM) 연동 모듈 - 뼈대만 제공

확인된 사실:
- SSG는 자체 Open API(https://eapi.ssgadm.com)를 운영하며 "상품 API" 카테고리가 있습니다.
- 신세계몰/이마트몰이 SSG.COM으로 통합되어 있어, 같은 API로 두 채널 모두 다룰 수 있는 것으로
  보입니다.
- 쓱파트너스(https://partners.ssgadm.com) 입점 계약 후 인증키를 발급받는 구조로 보입니다.

이번 조사로 확인 못한 것: 정확한 엔드포인트 경로, 인증 헤더 형식, 요청/응답 필드명.

API 신청: https://eapi.ssgadm.com/info/apiGuide.ssg (쓱파트너스 계정 필요)
"""
from __future__ import annotations

from ._gated_scaffold import not_yet_implemented


class SsgClient:
    def __init__(self, api_key: str | None = None, seller_id: str | None = None, **kwargs):
        self.api_key = api_key
        self.seller_id = seller_id

    def search_products(self, keyword: str | None = None) -> list[dict]:
        not_yet_implemented("SSG(신세계/이마트)", "https://eapi.ssgadm.com/info/apiGuide.ssg")
