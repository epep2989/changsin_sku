"""
네이버 커머스 API(스마트스토어) 연동 모듈

- 발급: https://apicenter.commerce.naver.com (네이버 커머스 API 센터)에서 애플리케이션 등록 후
  Client ID / Client Secret 발급
- 인증 방식: bcrypt 서명 기반 OAuth2 client_credentials
  sign = base64(bcrypt(f"{client_id}_{timestamp}", client_secret))
  (client_secret 자체가 bcrypt salt 형식으로 발급됩니다)
- 상품 검색: POST /external/v1/products/search, 요청 본문은 JSON.
  (GET + 쿼리파라미터 방식이 아님 — 공식 예제/이슈 트래커 기준으로 확인됨)
  주로 판매자 상품코드(sellerManagementCode, = 품목코드)로 검색합니다. 이 API는
  자유 텍스트 상품명 검색은 지원하지 않아서, 상품명으로 넣으면 못 찾을 수 있습니다
  (그럴 땐 품목코드로 검색해주세요).

주의:
- 네이버 쪽 응답 구조가 계정/시점별로 조금씩 다를 수 있어, 아래 파싱 로직은
  여러 가능한 필드명을 다 시도하는 방식으로 작성했습니다. 혹시 결과가 하나도 안 뜨는데
  실제로는 상품이 있다면, 한 번 원본 응답(raw)을 로그로 찍어서 필드명을 맞춰주세요.
"""
from __future__ import annotations

import base64
import time

import bcrypt
import requests

TOKEN_URL = "https://api.commerce.naver.com/external/v1/oauth2/token"
PRODUCT_SEARCH_URL = "https://api.commerce.naver.com/external/v1/products/search"


class NaverCommerceClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._token_expiry = 0.0

    def _make_signature(self, timestamp: int) -> str:
        password = f"{self.client_id}_{timestamp}".encode("utf-8")
        hashed = bcrypt.hashpw(password, self.client_secret.encode("utf-8"))
        return base64.b64encode(hashed).decode("utf-8")

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry:
            return self._token

        timestamp = int(time.time() * 1000)
        sign = self._make_signature(timestamp)
        payload = {
            "client_id": self.client_id,
            "timestamp": timestamp,
            "grant_type": "client_credentials",
            "client_secret_sign": sign,
            "type": "SELF",
        }
        resp = requests.post(TOKEN_URL, data=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + int(data.get("expires_in", 3600)) - 60
        return self._token

    def search_products(self, keyword: str | None = None, size: int = 50) -> list[dict]:
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body: dict = {"page": 1, "size": size}
        if keyword:
            # 품목코드(판매자 상품코드) 기준으로 검색. 이 API는 상품명 자유검색은 지원하지 않습니다.
            body["sellerManagementCode"] = keyword

        resp = requests.post(PRODUCT_SEARCH_URL, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # 응답이 {"contents": [...]} 형태이고, 각 항목이 바로 상품 정보이거나
        # {"channelProducts": [...]} 로 한 번 더 감싸져 있을 수 있어 둘 다 처리합니다.
        top_items = data.get("contents") or data.get("content") or data.get("data") or []
        if isinstance(top_items, dict):
            top_items = [top_items]

        results = []
        for item in top_items:
            nested = item.get("channelProducts") if isinstance(item, dict) else None
            entries = nested if nested else [item]
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                results.append(
                    {
                        "platform": "네이버",
                        "product_name": (
                            entry.get("name")
                            or entry.get("productName")
                            or (item.get("name") if isinstance(item, dict) else None)
                        ),
                        "product_id": (
                            entry.get("sellerManagementCode")
                            or entry.get("channelProductNo")
                            or entry.get("id")
                        ),
                        "status": entry.get("statusType") or entry.get("status"),
                        "raw": entry,
                    }
                )
        return results
