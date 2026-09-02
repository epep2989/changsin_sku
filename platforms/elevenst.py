"""
11번가 Open API 연동 모듈

- 발급: https://openapi.11st.co.kr (OPENAPI CENTER, 셀러 계정으로 API 키 신청)
- 인증 방식: API 키를 URL 쿼리 파라미터(key=)로 전달
- 응답 형식: XML, cp949(EUC-KR 계열) 인코딩

주의:
- 공개된 예제 기준으로 작성했으며, 응답 XML의 정확한 태그명(상품명/상태/상품코드에 해당하는
  태그)은 계정 발급 후 첫 응답을 직접 확인해서 맞춰야 할 가능성이 높습니다.
- 아래 search_products()는 파싱에 실패하거나 원하는 태그를 못 찾으면 raw XML을 함께 반환하니,
  처음 실행 시 raw 값을 출력해서 실제 태그 구조를 확인하세요.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import requests

BASE_URL = "http://openapi.11st.co.kr/openapi/OpenApiService.tmall"

# 실제 응답에서 확인되는 대로 이 리스트를 조정하세요.
NAME_TAGS = ("ProductName", "productName", "Name")
ID_TAGS = ("ProductNo", "ProductCode", "productNo", "prdNo")
STATUS_TAGS = ("SaleStatus", "SellStatus", "status")


def _first_text(elem, tags):
    for tag in tags:
        found = elem.find(f".//{tag}")
        if found is not None and found.text:
            return found.text
    return None


class ElevenstClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_products(self, keyword: str) -> list[dict]:
        params = {"key": self.api_key, "apiCode": "ProductSearch", "keyword": keyword}
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()

        text = resp.content.decode("cp949", errors="replace")
        results = []
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            # 파싱 실패 시 원문을 그대로 보여줘서 원인 파악을 돕습니다.
            return [
                {
                    "platform": "11번가",
                    "product_name": "(XML 파싱 실패 - raw 확인 필요)",
                    "product_id": None,
                    "status": None,
                    "raw": text,
                }
            ]

        if root.tag in ("ErrorResponse", "Error"):
            code = root.findtext("ErrorCode", default="")
            msg = root.findtext("ErrorMessage", default="") or root.findtext("ErrorDetail", default="")
            raise RuntimeError(f"11번가 API 오류 [{code}] {msg}".strip())

        products = root.findall(".//Product") or root.findall(".//product")
        for p in products:
            results.append(
                {
                    "platform": "11번가",
                    "product_name": _first_text(p, NAME_TAGS),
                    "product_id": _first_text(p, ID_TAGS),
                    "status": _first_text(p, STATUS_TAGS) or "상태태그 확인필요",
                    "raw": ET.tostring(p, encoding="unicode"),
                }
            )
        return results
