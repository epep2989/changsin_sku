"""
토스쇼핑 연동 모듈 - 뼈대만 제공

확인된 사실:
- 토스(비바리퍼블리카)가 운영하는 "토스쇼핑"에 공식 개발자 문서(https://shopping-docs.toss.im/dev)가
  있고, "연동 키" 발급 개념이 있습니다 (https://shopping-docs.toss.im/support/solution-api 참고).
- https://toss.im/shopping-seller 를 통해 입점을 신청합니다.

이번 조사로 확인 못한 것: 정확한 엔드포인트, 인증 헤더 형식, 요청/응답 필드명.

입점/연동 신청: https://toss.im/shopping-seller , 문서: https://shopping-docs.toss.im/dev
"""
from __future__ import annotations

from ._gated_scaffold import not_yet_implemented


class TossShoppingClient:
    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = api_key

    def search_products(self, keyword: str | None = None) -> list[dict]:
        not_yet_implemented("토스쇼핑", "https://shopping-docs.toss.im/dev")
