"""
인터파크 닷넷 연동 모듈 - 뼈대만 제공

확인된 사실:
- 인터파크 판매자센터(https://sellercenter.interpark.com)에 "상품 API 신청",
  "주문 API 신청" 절차가 공식적으로 안내되어 있습니다.
- 판매자매니저(https://seller.interpark.com) 가입 후 판매자센터에서 API를 신청하는
  승인 기반 구조입니다.

이번 조사로 확인 못한 것: 정확한 엔드포인트 경로, 인증 방식, 요청/응답 필드명
(신청 승인 후에만 상세 문서가 열리는 구조로 보입니다).

API 신청: https://sellercenter.interpark.com (판매자센터 계정 필요)
"""
from __future__ import annotations

from ._gated_scaffold import not_yet_implemented


class InterparkClient:
    def __init__(self, api_key: str | None = None, seller_id: str | None = None, **kwargs):
        self.api_key = api_key
        self.seller_id = seller_id

    def search_products(self, keyword: str | None = None) -> list[dict]:
        not_yet_implemented("인터파크", "https://sellercenter.interpark.com")
