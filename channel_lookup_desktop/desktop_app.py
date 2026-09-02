"""
창신리빙 입점현황 조회 - 데스크탑 프로그램 (검색형)

바탕화면 아이콘을 더블클릭하면 이 화면이 뜹니다.
같은 폴더에 있는 config.json 에서 채널별 API 키를 읽어와서,
품목코드/상품명 하나를 여러 채널에 동시에 검색합니다.

인터넷 사이트 버전과 다른 점:
- 회사 컴퓨터에서 직접 실행되기 때문에 매달 내는 호스팅 비용이 없습니다.
- 이 컴퓨터에서만 실행됩니다 (팀원이 같이 쓰려면 각자 설치해야 해요).
"""
from __future__ import annotations

import json
import os
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import font as tkfont
from tkinter import messagebox, scrolledtext, simpledialog
from urllib.parse import parse_qs, urlencode, urlparse

# .exe로 묶였을 때(PyInstaller)와 그냥 python으로 실행할 때 모두
# 이 프로그램과 같은 폴더를 기준으로 platforms/, config.json 을 찾도록 처리합니다.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

from platforms.cafe24 import Cafe24Client  # noqa: E402
from platforms.coupang import CoupangClient  # noqa: E402
from platforms.elevenst import ElevenstClient  # noqa: E402
from platforms.naver import NaverCommerceClient  # noqa: E402

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

CONFIG_TEMPLATE = {
    "coupang": {"access_key": "", "secret_key": "", "vendor_id": ""},
    "naver_stores": [
        {"store_name": "네이버", "client_id": "", "client_secret": ""}
    ],
    "elevenst": {"api_key": ""},
    "cafe24": {
        "mall_id": "",
        "client_id": "",
        "client_secret": "",
        "access_token": "",
        "refresh_token": "",
    },
}


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def ensure_config_file() -> None:
    """config.json이 아예 없으면, 빈 틀을 하나 만들어둡니다(처음 실행 시)."""
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(CONFIG_TEMPLATE, f, ensure_ascii=False, indent=2)


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


CAFE24_REDIRECT_PATH = "/order/basket.html"
CAFE24_SCOPE = "mall.read_product"


def build_cafe24_authorize_url(mall_id: str, client_id: str) -> tuple[str, str]:
    """카페24 로그인/승인 페이지 주소를 만듭니다. (redirect_uri, 실제 URL) 을 돌려줍니다."""
    redirect_uri = f"https://{mall_id}.cafe24.com{CAFE24_REDIRECT_PATH}"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "state": "csn_channel_lookup",
        "redirect_uri": redirect_uri,
        "scope": CAFE24_SCOPE,
    }
    url = f"https://{mall_id}.cafe24api.com/api/v2/oauth/authorize?{urlencode(params)}"
    return redirect_uri, url


def extract_auth_code(pasted: str) -> str:
    """사용자가 코드만 붙여넣었을 수도 있고, 리다이렉트된 주소 전체를 붙여넣었을
    수도 있어서 둘 다 처리합니다."""
    pasted = (pasted or "").strip()
    if "code=" in pasted:
        parsed = urlparse(pasted)
        qs = parse_qs(parsed.query)
        if "code" in qs and qs["code"]:
            return qs["code"][0]
    return pasted


def naver_accounts(cfg: dict) -> list[tuple[str, str, str]]:
    accounts: list[tuple[str, str, str]] = []
    for store in cfg.get("naver_stores", []) or []:
        client_id = (store.get("client_id") or "").strip()
        if not client_id:
            continue
        name = store.get("store_name") or "네이버"
        accounts.append((name, client_id, store.get("client_secret") or ""))
    return accounts


def run_search(keyword: str, cfg: dict) -> tuple[list[dict], list[str]]:
    results: list[dict] = []
    errors: list[str] = []

    coupang = cfg.get("coupang") or {}
    if coupang.get("access_key"):
        try:
            client = CoupangClient(
                coupang["access_key"], coupang.get("secret_key", ""), coupang.get("vendor_id", "")
            )
            results += client.search_products(keyword=keyword)
        except Exception as e:  # noqa: BLE001
            errors.append(f"[쿠팡] {e}")

    for store_name, client_id, client_secret in naver_accounts(cfg):
        try:
            client = NaverCommerceClient(client_id, client_secret)
            r = client.search_products(keyword=keyword)
            for item in r:
                item["platform"] = store_name
            results += r
        except Exception as e:  # noqa: BLE001
            errors.append(f"[{store_name}] {e}")

    elevenst = cfg.get("elevenst") or {}
    if elevenst.get("api_key"):
        try:
            client = ElevenstClient(elevenst["api_key"])
            results += client.search_products(keyword)
        except Exception as e:  # noqa: BLE001
            errors.append(f"[11번가] {e}")

    cafe24 = cfg.get("cafe24") or {}
    if cafe24.get("mall_id"):
        try:
            client = Cafe24Client(
                cafe24["mall_id"],
                cafe24.get("client_id", ""),
                cafe24.get("client_secret", ""),
                access_token=cafe24.get("access_token") or None,
                refresh_token=cafe24.get("refresh_token") or None,
            )
            results += client.search_products(keyword=keyword)
        except Exception as e:  # noqa: BLE001
            errors.append(f"[카페24] {e}")

    return results, errors


def configured_platforms(cfg: dict) -> list[str]:
    names: list[str] = []
    if (cfg.get("coupang") or {}).get("access_key"):
        names.append("쿠팡")
    names += [n for n, _, _ in naver_accounts(cfg)]
    if (cfg.get("elevenst") or {}).get("api_key"):
        names.append("11번가")
    if (cfg.get("cafe24") or {}).get("mall_id"):
        names.append("카페24")
    return names


FONT_NAME_CANDIDATES = ["맑은 고딕", "Malgun Gothic", "AppleGothic", "Noto Sans CJK KR"]


def pick_font(root: tk.Tk) -> str:
    available = set(tkfont.families(root))
    for name in FONT_NAME_CANDIDATES:
        if name in available:
            return name
    return "TkDefaultFont"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("창신리빙 입점현황 조회")
        self.geometry("760x600")
        self.minsize(600, 480)
        self.configure(bg="#f4f6f8")

        ensure_config_file()
        self.cfg = load_config()

        base_font = pick_font(self)
        self.f_title = (base_font, 19, "bold")
        self.f_sub = (base_font, 10)
        self.f_input = (base_font, 14)
        self.f_btn = (base_font, 12, "bold")
        self.f_result = (base_font, 11)
        self.f_small = (base_font, 9)

        self._build_ui()
        self._refresh_configured_label()

    def _build_ui(self):
        header = tk.Label(
            self, text="🔎 창신리빙 입점현황 조회", font=self.f_title, bg="#f4f6f8", fg="#1a1a1a"
        )
        header.pack(pady=(20, 2))

        self.sub_label = tk.Label(self, text="", font=self.f_sub, fg="#666", bg="#f4f6f8")
        self.sub_label.pack(pady=(0, 14))

        entry_frame = tk.Frame(self, bg="#f4f6f8")
        entry_frame.pack(pady=4, padx=20, fill="x")

        self.entry = tk.Entry(entry_frame, font=self.f_input, relief="solid", bd=1)
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.on_search())
        self.entry.focus_set()

        self.search_btn = tk.Button(
            entry_frame,
            text="검색",
            font=self.f_btn,
            bg="#3B6EF6",
            fg="white",
            activebackground="#2f57c9",
            activeforeground="white",
            relief="flat",
            command=self.on_search,
            width=8,
        )
        self.search_btn.pack(side="left", ipady=6)

        btn_row = tk.Frame(self, bg="#f4f6f8")
        btn_row.pack(pady=(6, 12))

        settings_btn = tk.Button(
            btn_row,
            text="⚙ API 키 설정 파일 열기",
            font=self.f_small,
            relief="flat",
            fg="#3B6EF6",
            bg="#f4f6f8",
            cursor="hand2",
            command=self.open_settings,
        )
        settings_btn.pack(side="left", padx=8)

        cafe24_btn = tk.Button(
            btn_row,
            text="🔗 카페24 연결하기 (최초 1회)",
            font=self.f_small,
            relief="flat",
            fg="#3B6EF6",
            bg="#f4f6f8",
            cursor="hand2",
            command=self.start_cafe24_authorize,
        )
        cafe24_btn.pack(side="left", padx=8)

        result_frame = tk.Frame(self, bg="#ffffff", highlightbackground="#e2e5e9", highlightthickness=1)
        result_frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        self.result_box = scrolledtext.ScrolledText(
            result_frame, font=self.f_result, wrap="word", bd=0, padx=14, pady=12
        )
        self.result_box.pack(fill="both", expand=True)
        self.result_box.configure(state="disabled")
        self._write_placeholder()

    def _refresh_configured_label(self):
        configured = configured_platforms(self.cfg)
        if configured:
            text = "지금 검색되는 채널: " + ", ".join(configured)
        else:
            text = "지금 검색되는 채널: 없음 — 아래 'API 키 설정 파일 열기'로 먼저 채워주세요."
        self.sub_label.configure(text=text)

    def _write_placeholder(self):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert(
            "end", "품목코드나 상품명을 입력하고 검색을 눌러주세요.\n(엔터 키로도 검색돼요)"
        )
        self.result_box.configure(state="disabled")

    def on_search(self):
        keyword = self.entry.get().strip()
        if not keyword:
            return
        self.cfg = load_config()  # 설정을 방금 바꿨을 수도 있으니 매번 새로 읽음
        self._refresh_configured_label()
        self.search_btn.configure(state="disabled", text="검색 중")
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", f'"{keyword}" 검색 중...\n')
        self.result_box.configure(state="disabled")
        threading.Thread(target=self._do_search, args=(keyword,), daemon=True).start()

    def _do_search(self, keyword: str):
        try:
            results, errors = run_search(keyword, self.cfg)
        except Exception as e:  # noqa: BLE001
            results, errors = [], [f"[전체] 알 수 없는 오류: {e}"]
        self.after(0, self._show_results, keyword, results, errors)

    def _show_results(self, keyword: str, results: list[dict], errors: list[str]):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", f'"{keyword}" 검색 결과\n\n')
        if results:
            for r in results:
                platform = r.get("platform", "?")
                name = r.get("product_name") or "-"
                status = r.get("status") or "-"
                pid = r.get("product_id") or "-"
                self.result_box.insert(
                    "end", f"✅ [{platform}]  {name}\n     상태: {status}   코드: {pid}\n\n"
                )
        else:
            self.result_box.insert("end", "지금 검색 가능한 채널에서는 찾지 못했어요.\n\n")
        if errors:
            self.result_box.insert("end", "확인 안 된 채널:\n")
            for e in errors:
                self.result_box.insert("end", f"⚠ {e}\n")
        self.result_box.insert(
            "end",
            "\n---\n이 화면에서 검색되는 채널은 API 키가 등록된 채널만이에요. "
            "나머지는 회사의 '수기확인 체크리스트' 엑셀을 참고해주세요.",
        )
        self.result_box.configure(state="disabled")
        self.search_btn.configure(state="normal", text="검색")

    def start_cafe24_authorize(self):
        self.cfg = load_config()
        cafe24 = self.cfg.get("cafe24") or {}
        mall_id = (cafe24.get("mall_id") or "").strip()
        client_id = (cafe24.get("client_id") or "").strip()
        client_secret = (cafe24.get("client_secret") or "").strip()

        if not (mall_id and client_id and client_secret):
            messagebox.showwarning(
                "카페24 연결",
                "먼저 config.json의 cafe24 항목에 mall_id / client_id / client_secret\n"
                "세 가지를 채워넣고 저장한 다음, 다시 눌러주세요.",
            )
            return

        redirect_uri, url = build_cafe24_authorize_url(mall_id, client_id)
        try:
            webbrowser.open(url)
        except Exception:
            pass

        info = (
            "브라우저가 열렸을 거예요.\n\n"
            "1) 카페24 관리자 계정으로 로그인하고, 권한 승인(허용) 버튼을 눌러주세요.\n"
            "2) 승인하면 이상한 페이지(장바구니 화면 등)로 이동하는데, 정상이에요.\n"
            "3) 그 화면의 주소창(맨 위 URL) 전체를 복사해서, 다음 창에 붙여넣어 주세요.\n\n"
            "브라우저가 안 열렸다면 이 주소를 직접 복사해서 여세요:\n" + url
        )
        messagebox.showinfo("카페24 연결 - 1단계", info)

        pasted = simpledialog.askstring(
            "카페24 연결 - 2단계",
            "승인 후 이동한 페이지의 주소창(URL) 전체를 여기에 붙여넣어 주세요:",
            parent=self,
        )
        if not pasted:
            return

        code = extract_auth_code(pasted)
        if not code:
            messagebox.showerror("카페24 연결 실패", "주소에서 인증 코드를 찾지 못했어요. 다시 시도해주세요.")
            return

        try:
            access_token, refresh_token = Cafe24Client.exchange_authorization_code(
                mall_id, client_id, client_secret, code, redirect_uri
            )
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(
                "카페24 연결 실패",
                f"토큰 교환 중 오류가 발생했어요:\n{e}\n\n"
                "인증 코드는 발급 후 짧은 시간 안에만 쓸 수 있어요. "
                "'카페24 연결하기' 버튼을 다시 눌러 처음부터 시도해주세요.",
            )
            return

        self.cfg.setdefault("cafe24", {})
        self.cfg["cafe24"]["access_token"] = access_token
        self.cfg["cafe24"]["refresh_token"] = refresh_token
        save_config(self.cfg)
        messagebox.showinfo("카페24 연결 완료", "연결됐어요! 이제 검색해보시면 카페24 결과도 같이 나와요.")
        self._refresh_configured_label()

    def open_settings(self):
        answer = messagebox.askyesno(
            "API 키 설정",
            "이 프로그램과 같은 폴더에 있는 config.json 파일을 열어서\n"
            "채널별 API 키를 입력한 뒤 저장하고, 다시 검색해보세요.\n\n"
            f"파일 위치:\n{CONFIG_PATH}\n\n"
            "지금 그 폴더를 열어드릴까요?",
        )
        if answer:
            try:
                if sys.platform.startswith("win"):
                    os.startfile(BASE_DIR)  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    os.system(f'open "{BASE_DIR}"')
                else:
                    webbrowser.open(BASE_DIR)
            except Exception:
                pass


if __name__ == "__main__":
    App().mainloop()
