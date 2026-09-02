"""
ESM PLUS (G마켓 / 옥션) 연동 모듈 - 뼈대만 제공

ESM PLUS Open API는 다른 채널과 달리:
1) ESM PLUS 내에서 '마스터 ID' 발급 및 Open API 이용 신청(승인 필요)이 먼저 필요하고,
2) 인증에 JWT(발급받은 secret key로 서명)를 사용하며,
3) 상품 조회 관련 정확한 엔드포인트가 공개 문서에 상세히 나와있지 않아
   (https://etapi.gmarket.com 참고, 승인 후 제공되는 문서 확인 필요)
   신청 승인 후 실제 문서를 보고 구현을 완성해야 합니다.

지금 단계에서는 잘못된 엔드포인트로 동작하는 것처럼 보이는 코드를 두는 것보다,
연동이 필요해지면 알려주시면 그때 실제 문서를 보고 이어서 구현하는 쪽을 권장합니다.

대안:
- G마켓/옥션은 사방넷·이지어드민·플레이오토 같은 기존 통합관리 솔루션들이 이미
  ESM PLUS 연동을 지원하므로, 이 채널만큼은 그런 솔루션을 통해 조회하는 것도
  현실적인 방법입니다.
"""
from __future__ import annotations


def search_products(keyword: str, config: dict | None = None) -> list[dict]:
    raise NotImplementedError(
        "ESM PLUS(G마켓/옥션) 연동은 아직 구현되지 않았습니다. "
        "ESM PLUS에서 Open API 이용 신청 및 승인을 받은 뒤, "
        "발급되는 문서를 보고 이어서 구현이 필요합니다."
    )
