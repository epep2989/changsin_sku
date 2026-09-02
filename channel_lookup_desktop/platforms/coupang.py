"""
쿠팡 Open API (Wing 판매자센터) 연동 모듈

- 발급: WING 판매자센터 > 확장 서비스 > Open API 키 발급
- 공식 문서: https://developers.coupang.com/ko/getting-started/coupang-open-api
- 인증 방식: HMAC-SHA256 서명 (CEA 알고리즘). access-key/secret-key는 절대 코드에 직접 넣지 말고
  config.json 등 외부 설정 파일로 관리하세요.

주의:
- 이 모듈은 공식 문서 기준으로 작성했지만, 세부 파라미터/응답 필드명은 계정별·시점별로
  달라질 수 있습니다. 처음 실행 시 raw 응답(response.json())을 한 번 print 해서
  실제 필드명과 맞는지 확인하는 것을 권장합니다.
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests

BASE_URL = "https://api-gateway.coupang.com"
PRODUCT_SEARCH_PATH = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"


class CoupangClient:
    def __init__(self, access_key: str, secret_key: str, vendor_id: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.vendor_id = vendor_id

    def _signature(self, method: str, path: str, query: str) -> tuple[str, str]:
        signed_date = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
        message = signed_date + method + path + query
        signature = hmac.new(
            self.secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return signed_date, signature

    def _headers(self, method: str, path: str, query: str) -> dict:
        signed_date, signature = self._signature(method, path, query)
        authorization = (
            f"CEA algorithm=HmacSHA256, access-key={self.access_key}, "
            f"signed-date={signed_date}, signature={signature}"
        )
        return {
            "Authorization": authorization,
            "Content-Type": "application/json;charset=UTF-8",
        }

    def search_products(
        self,
        keyword: str | None = None,
        seller_product_id: str | None = None,
        max_per_page: int = 50,
    ) -> list[dict]:
        """품목코드(sellerProductId) 또는 상품명(sellerProductName, 20자 이하)으로 검색합니다."""
        params = {"vendorId": self.vendor_id, "maxPerPage": max_per_page}
        if seller_product_id:
            params["sellerProductId"] = seller_product_id
        elif keyword:
            # 쿠팡 API는 상품명 검색 시 20자 제한이 있습니다.
            params["sellerProductName"] = keyword[:20]

        query = urlencode(params)
        headers = self._headers("GET", PRODUCT_SEARCH_PATH, query)
        url = f"{BASE_URL}{PRODUCT_SEARCH_PATH}?{query}"

        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("data", []) or []:
            results.append(
                {
                    "platform": "쿠팡",
                    "product_name": item.get("sellerProductName"),
                    "product_id": item.get("sellerProductId"),
                    "status": item.get("statusName"),
                    "raw": item,
                }
            )
        return results
