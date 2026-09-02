"""
환경변수(Render의 Environment Variables)에서 각 채널 열쇠(API 키)를 읽어와서
품목코드/상품명 하나를 여러 채널에 동시에 검색하는 핵심 로직.

app.py(웹 화면)가 이 파일의 run_search()를 호출합니다.
"""
from __future__ import annotations

import os

from platforms import esm
from platforms.cafe24 import Cafe24Client
from platforms.cjonstyle import CjOnstyleClient
from platforms.coupang import CoupangClient
from platforms.elevenst import ElevenstClient
from platforms.interpark import InterparkClient
from platforms.kakao import KakaoShoppingClient
from platforms.lotteon import LotteOnClient
from platforms.naver import NaverCommerceClient
from platforms.ssg import SsgClient
from platforms.toss import TossShoppingClient

PLATFORM_ORDER = [
    "쿠팡",
    "네이버",
    "11번가",
    "카페24",
    "G마켓/옥션",
    "롯데ON",
    "SSG(신세계/이마트)",
    "인터파크",
    "CJ온스타일",
    "카카오쇼핑(선물하기/톡스토어)",
    "토스쇼핑",
]


def _env(name: str) -> str | None:
    val = os.environ.get(name)
    return val if val else None


def run_search(keyword: str) -> tuple[list[dict], list[str]]:
    """환경변수에 값이 채워진 채널만 자동으로 검색합니다. 결과 목록과 에러 메시지 목록을 반환."""
    all_results: list[dict] = []
    errors: list[str] = []

    # 쿠팡
    if _env("COUPANG_ACCESS_KEY"):
        try:
            client = CoupangClient(_env("COUPANG_ACCESS_KEY"), _env("COUPANG_SECRET_KEY"), _env("COUPANG_VENDOR_ID"))
            all_results += client.search_products(keyword=keyword)
        except Exception as e:  # noqa: BLE001
            errors.append(f"[쿠팡] {e}")

    # 네이버
    if _env("NAVER_CLIENT_ID"):
        try:
            client = NaverCommerceClient(_env("NAVER_CLIENT_ID"), _env("NAVER_CLIENT_SECRET"))
            all_results += client.search_products(keyword=keyword)
        except Exception as e:  # noqa: BLE001
            errors.append(f"[네이버] {e}")

    # 11번가
    if _env("ELEVENST_API_KEY"):
        try:
            client = ElevenstClient(_env("ELEVENST_API_KEY"))
            all_results += client.search_products(keyword)
        except Exception as e:  # noqa: BLE001
            errors.append(f"[11번가] {e}")

    # 카페24
    if _env("CAFE24_MALL_ID"):
        try:
            client = Cafe24Client(
                _env("CAFE24_MALL_ID"),
                _env("CAFE24_CLIENT_ID"),
                _env("CAFE24_CLIENT_SECRET"),
                access_token=_env("CAFE24_ACCESS_TOKEN"),
                refresh_token=_env("CAFE24_REFRESH_TOKEN"),
            )
            all_results += client.search_products(keyword=keyword)
        except Exception as e:  # noqa: BLE001
            errors.append(f"[카페24] {e}")

    # G마켓/옥션 (뼈대만 구현됨 - 값이 있으면 시도만 하고 안내 메시지가 뜸)
    if _env("ESM_ENABLED") == "true":
        try:
            all_results += esm.search_products(keyword, {})
        except Exception as e:  # noqa: BLE001
            errors.append(f"[G마켓/옥션] {e}")

    gated = [
        ("LOTTEON_ENABLED", "롯데ON", LotteOnClient),
        ("SSG_ENABLED", "SSG(신세계/이마트)", SsgClient),
        ("INTERPARK_ENABLED", "인터파크", InterparkClient),
        ("CJONSTYLE_ENABLED", "CJ온스타일", CjOnstyleClient),
        ("KAKAO_ENABLED", "카카오쇼핑(선물하기/톡스토어)", KakaoShoppingClient),
        ("TOSS_ENABLED", "토스쇼핑", TossShoppingClient),
    ]
    for env_key, label, client_cls in gated:
        if _env(env_key) == "true":
            try:
                client = client_cls()
                all_results += client.search_products(keyword=keyword)
            except Exception as e:  # noqa: BLE001
                errors.append(f"[{label}] {e}")

    return all_results, errors


def configured_platforms() -> list[str]:
    """지금 열쇠가 채워져 있어서 실제로 검색되는 채널 이름 목록 (화면에 안내용으로 보여줌)."""
    names = []
    if _env("COUPANG_ACCESS_KEY"):
        names.append("쿠팡")
    if _env("NAVER_CLIENT_ID"):
        names.append("네이버")
    if _env("ELEVENST_API_KEY"):
        names.append("11번가")
    if _env("CAFE24_MALL_ID"):
        names.append("카페24")
    return names
