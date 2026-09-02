"""
네이버 커머스 API(스마트스토어) 연동 모듈

- 발급: https://apicenter.commerce.naver.com (네이버 커머스 API 센터)에서 애플리케이션 등록 후
  Client ID / Client Secret 발급
- 인증 방식: bcrypt 서명 기반 OAuth2 client_credentials
  sign = base64(bcrypt(f"{client_id}_{timestamp}", client_secret))
  (client_secret 자체가 bcrypt salt 형식으로 발급됩니다)

주의:
- 상품 조회 엔드포인트/파라미터는 네이버 커머스 API가 몇 차례 개편된 이력이 있어,
  실행 전 반드시 최신 공식 문서(https://apicenter.commerce.naver.com/docs)에서
  '상품 목록 조회' 또는 '상품 검색' API의 정확한 path/method/파라미터명을 확인하고
  아래 PRODUCT_SEARCH_PATH 및 search_products()의 파라미터를 맞춰주세요.
- 이 모듈은 토큰 발급까지는 신뢰도 높게 작성되어 있고, 상품 조회 부분은 베스트에포트
  템플릿입니다.
"""
from __future__ import annotations

import base64
import time

import bcrypt
import requests

TOKEN_URL = "https://api.commerce.naver.com/external/v1/oauth2/token"
BASE_URL = "https://api.commerce.naver.com/external"

# TODO: 최신 문서 기준으로 실제 상품 검색 경로를 확인해서 필요시 수정하세요.
PRODUCT_SEARCH_PATH = "/v1/products/search"


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
        headers = {"Authorization": f"Bearer {token}"}
        params = {"page": 1, "size": size}
        if keyword:
            # 정확한 파라미터명(productName, searchKeyword 등)은 최신 문서로 확인 필요
            params["searchKeyword"] = keyword

        url = f"{BASE_URL}{PRODUCT_SEARCH_PATH}"
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        items = data.get("contents") or data.get("content") or data.get("data") or []
        for item in items:
            results.append(
                {
                    "platform": "네이버",
                    "product_name": item.get("name") or item.get("productName"),
                    "product_id": item.get("sellerManagementCode") or item.get("id"),
                    "status": item.get("statusType") or item.get("status"),
                    "raw": item,
                }
            )
        return results
