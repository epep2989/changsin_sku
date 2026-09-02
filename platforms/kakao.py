"""
카카오쇼핑(선물하기 / 톡스토어) 연동 모듈 - 뼈대만 제공

확인된 사실:
- 카카오쇼핑 Open API(https://shopping-developers.kakao.com)가 공식 제공되며,
  선물하기/톡스토어의 상품 등록/조회, 주문 조회/처리를 지원합니다.
- "대형제휴사, 브랜드, 대행사, 호스팅사 등"을 대상으로 별도 이용 신청(연동 검토 요청)을
  거쳐야 사용할 수 있습니다. 즉시 셀프서비스 발급은 아닙니다.

이번 조사로 확인 못한 것: 정확한 인증 방식(API 키/OAuth 여부), 엔드포인트, 요청/응답 필드명
(신청 승인 후에만 상세 문서가 열리는 구조로 보입니다).

이용 신청: https://shopping-developers.kakao.com
"""
from __future__ import annotations

from ._gated_scaffold import not_yet_implemented


class KakaoShoppingClient:
    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = api_key

    def search_products(self, keyword: str | None = None) -> list[dict]:
        not_yet_implemented("카카오쇼핑(선물하기/톡스토어)", "https://shopping-developers.kakao.com")
