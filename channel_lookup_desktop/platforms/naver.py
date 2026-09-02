"""
네이버 커머스 API(스마트스토어) 연동 모듈

- 발급: https://apicenter.commerce.naver.com (네이버 커머스 API 센터)에서 애플리케이션 등록 후
  Client ID / Client Secret 발급
- 인증 방식: bcrypt 서명 기반 OAuth2 client_credentials
  sign = base64(bcrypt(f"{client_id}_{timestamp}", client_secret))
  (client_secret 자체가 bcrypt salt 형식으로 발급됩니다)
- 상품 검색: POST /external/v1/products/search, 요청 본문은 JSON.
  (GET + 쿼리파라미터 방식이 아님)

중요 — 상품명 검색 방식:
  네이버 이 API는 "상품명을 이걸로 검색해줘" 같은 자유 텍스트 검색 파라미터를
  공식적으로 제공하지 않습니다 (판매자 상품코드/채널상품번호/날짜 등으로만 필터링).
  그래서 이 모듈은 대신 "전체 상품 목록을 페이지별로 쭉 가져온 다음,
  상품명 또는 코드에 검색어가 포함되는지 우리 쪽에서 직접 비교"하는 방식으로
  구현했습니다. 품목코드가 비어있는 상품도 상품명으로 잘 찾아집니다.
  (스토어 상품이 아주 많으면 첫 검색이 몇 초~수십 초 걸릴 수 있어요.)

주의:
- 네이버 쪽 응답 구조가 계정/시점별로 조금씩 다를 수 있어, 아래 파싱 로직은
  여러 가능한 필드명을 다 시도하는 방식으로 작성했습니다.
"""
from __future__ import annotations

import base64
import time

import bcrypt
import requests

TOKEN_URL = "https://api.commerce.naver.com/external/v1/oauth2/token"
PRODUCT_SEARCH_URL = "https://api.commerce.naver.com/external/v1/products/search"

PAGE_SIZE = 50
MAX_PAGES = 60  # 안전장치: 스토어 상품이 아주 많아도 최대 이만큼(약 3000개)까지만 훑습니다.


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

    @staticmethod
    def _extract_entries(data: dict) -> list[dict]:
        """응답에서 상품 항목들을 뽑아냅니다. {"channelProducts": [...]} 로 한 번 더
        감싸져 있는 경우와, 바로 평평한 목록인 경우를 둘 다 처리합니다."""
        top_items = data.get("contents") or data.get("content") or data.get("data") or []
        if isinstance(top_items, dict):
            top_items = [top_items]

        entries: list[dict] = []
        for item in top_items:
            if not isinstance(item, dict):
                continue
            nested = item.get("channelProducts")
            candidates = nested if nested else [item]
            for entry in candidates:
                if isinstance(entry, dict):
                    entries.append(entry)
        return entries

    def search_products(self, keyword: str | None = None) -> list[dict]:
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        keyword_norm = (keyword or "").strip().lower()

        results: list[dict] = []
        page = 1
        while page <= MAX_PAGES:
            body = {"page": page, "size": PAGE_SIZE}
            resp = requests.post(PRODUCT_SEARCH_URL, headers=headers, json=body, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            entries = self._extract_entries(data)
            if not entries:
                break

            for entry in entries:
                name = entry.get("name") or entry.get("productName") or ""
                code = (
                    entry.get("sellerManagementCode")
                    or entry.get("channelProductNo")
                    or entry.get("id")
                    or ""
                )
                if keyword_norm:
                    if keyword_norm not in str(name).lower() and keyword_norm not in str(code).lower():
                        continue
                results.append(
                    {
                        "platform": "네이버",
                        "product_name": name or None,
                        "product_id": code or None,
                        "status": entry.get("statusType") or entry.get("status"),
                        "raw": entry,
                    }
                )

            if len(entries) < PAGE_SIZE:
                break  # 마지막 페이지
            page += 1

        return results
