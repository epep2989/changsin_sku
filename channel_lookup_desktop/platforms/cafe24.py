"""
카페24 Open API 연동 모듈 (자사몰 / 유튜브쇼핑 연동 등 카페24 기반 채널용)

- 발급: https://developers.cafe24.com 에서 앱 등록
  - "프라이빗 앱(Private App)"으로 등록하면 본인 쇼핑몰(mall_id) 관리자 승인만으로
    access_token/refresh_token이 바로 발급됩니다 (심사 없음, 가장 간단한 방법).
  - "퍼블릭 앱"으로 만들면 OAuth2 Authorization Code Flow(인가코드 → 토큰 교환)를
    거쳐야 합니다.
- 인증 방식: OAuth2 Bearer 토큰. access_token 유효기간 2시간, refresh_token 2주.
  만료되면 refresh_token으로 재발급.
- 공식 문서: https://developers.cafe24.com/docs/api/admin/

주의:
- 상품 검색 파라미터 중 product_no/brand_code/created_start_date 등은 공식 문서에
  명시적으로 확인했지만, 상품명(keyword) 검색 파라미터명(예: product_name)은
  이번 조사에서 문서 전문을 확인하지 못해 베스트에포트로 넣어뒀습니다. 실제 계정으로
  첫 조회 시 결과가 없으면 품목코드(product_code)로 검색하거나, 공식 API 레퍼런스에서
  정확한 파라미터명을 확인해주세요.
"""
from __future__ import annotations

import base64

import requests

API_VERSION = "2024-09-01"


class Cafe24Client:
    def __init__(
        self,
        mall_id: str,
        client_id: str,
        client_secret: str,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ):
        self.mall_id = mall_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.base_url = f"https://{mall_id}.cafe24api.com"

    def _refresh_access_token(self) -> None:
        if not self.refresh_token:
            raise RuntimeError(
                "access_token이 없거나 만료됐고 refresh_token도 없습니다. "
                "카페24 개발자센터에서 앱의 access_token/refresh_token을 다시 발급받아 "
                "config.json에 넣어주세요."
            )
        basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        resp = requests.post(
            f"{self.base_url}/api/v2/oauth/token",
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "refresh_token", "refresh_token": self.refresh_token},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Cafe24-Api-Version": API_VERSION,
        }

    @staticmethod
    def exchange_authorization_code(
        mall_id: str, client_id: str, client_secret: str, code: str, redirect_uri: str
    ) -> tuple[str, str]:
        """최초 1회만 필요: 브라우저에서 로그인/승인하고 받은 인가코드(code)를
        access_token/refresh_token으로 교환합니다. (퍼블릭 앱 OAuth2 플로우)"""
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        resp = requests.post(
            f"https://{mall_id}.cafe24api.com/api/v2/oauth/token",
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["access_token"], data.get("refresh_token", "")

    def search_products(
        self,
        keyword: str | None = None,
        product_code: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        if not self.access_token:
            self._refresh_access_token()

        params = {"limit": limit}
        if product_code:
            params["product_code"] = product_code
        elif keyword:
            # 공식 문서에서 명시적으로 확인하지 못한 파라미터입니다 (베스트에포트).
            params["product_name"] = keyword

        url = f"{self.base_url}/api/v2/admin/products"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=15)
        if resp.status_code == 401:
            self._refresh_access_token()
            resp = requests.get(url, headers=self._headers(), params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("products", []) or []:
            status_parts = []
            if item.get("selling") is not None:
                status_parts.append("판매중" if item.get("selling") == "T" else "판매안함")
            if item.get("display") is not None:
                status_parts.append("진열중" if item.get("display") == "T" else "진열안함")
            results.append(
                {
                    "platform": "카페24",
                    "product_name": item.get("product_name"),
                    "product_id": item.get("product_code") or item.get("product_no"),
                    "status": " / ".join(status_parts) or None,
                    "raw": item,
                }
            )
        return results
