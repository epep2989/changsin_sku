"""
롯데ON 연동 모듈 - 뼈대만 제공

확인된 사실:
- 롯데ON은 자체 API 센터(https://api.lotteon.com)를 운영하며,
  "상품 목록 조회" API가 명시적으로 존재합니다.
- 판매자(협력사) 계정으로 로그인 후 API 이용 신청 → 승인 후 인증키 발급받는 구조로 보입니다.

이번 조사로 확인 못한 것: 정확한 엔드포인트 경로, 인증 헤더 형식, 요청/응답 필드명.
(API 상세 페이지가 로그인 후 JS로 렌더링되는 방식이라 비로그인 상태로는 확인이 어려웠습니다.)

API 신청: https://api.lotteon.com/apiGuide/ (롯데ON 판매자센터 계정 필요)
"""
from __future__ import annotations

from ._gated_scaffold import not_yet_implemented


class LotteOnClient:
    def __init__(self, api_key: str | None = None, seller_id: str | None = None, **kwargs):
        self.api_key = api_key
        self.seller_id = seller_id

    def search_products(self, keyword: str | None = None) -> list[dict]:
        not_yet_implemented("롯데ON", "https://api.lotteon.com/apiGuide/")
