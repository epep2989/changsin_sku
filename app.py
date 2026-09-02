"""
창신리빙 - 품목코드/상품명으로 어느 채널에 팔리고 있는지 한 번에 확인하는 웹사이트.

사용법(팀원 입장):
1) 회사에서 알려준 주소로 들어간다.
2) 비밀번호를 입력한다.
3) 품목코드나 상품명을 입력하고 "검색" 버튼을 누른다.
4) 어느 채널에 있는지 화면에 바로 뜬다.

이 파일은 화면(웹페이지)만 담당하고, 실제 채널별 검색 로직은 channel_search.py 에 있습니다.
"""
from __future__ import annotations

import os
import secrets
from datetime import timedelta

from flask import Flask, redirect, render_template_string, request, session, url_for

from channel_search import PLATFORM_ORDER, configured_platforms, run_search

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(16)
app.permanent_session_lifetime = timedelta(days=30)

SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")

BASE_STYLE = """
<style>
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
    background: #f4f6f8; margin: 0; padding: 0; color: #222;
  }
  .wrap { max-width: 720px; margin: 0 auto; padding: 24px 16px 64px; }
  h1 { font-size: 22px; margin: 8px 0 4px; }
  p.sub { color: #666; font-size: 14px; margin-top: 0; }
  .card {
    background: #fff; border-radius: 14px; padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06); margin-bottom: 16px;
  }
  input[type=text], input[type=password], textarea {
    width: 100%; font-size: 18px; padding: 14px; border: 2px solid #dde2e7;
    border-radius: 10px; margin-top: 6px; margin-bottom: 14px; font-family: inherit;
  }
  textarea { min-height: 90px; resize: vertical; }
  label { font-weight: 600; font-size: 15px; }
  button {
    background: #2f6fed; color: #fff; border: none; border-radius: 10px;
    padding: 14px 22px; font-size: 18px; font-weight: 700; cursor: pointer; width: 100%;
  }
  button:hover { background: #1f56c9; }
  .error { background: #fdecea; color: #b3261e; padding: 12px 14px; border-radius: 10px; margin-bottom: 14px; font-size: 14px; }
  .muted { color: #888; font-size: 13px; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 14px; }
  th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid #eee; }
  th { color: #555; font-size: 12px; }
  .badge { display: inline-block; padding: 3px 9px; border-radius: 999px; font-size: 12px; font-weight: 600; }
  .badge-ok { background: #e6f4ea; color: #1e7e34; }
  .badge-none { background: #f1f1f1; color: #999; }
  .code-title { font-size: 16px; font-weight: 700; margin: 22px 0 4px; }
  .logout { text-align: right; margin-bottom: 8px; }
  .logout a { color: #888; font-size: 13px; text-decoration: none; }
  .footer-note { font-size: 12px; color: #aaa; margin-top: 30px; line-height: 1.6; }
</style>
"""

LOGIN_HTML = """
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>창신리빙 입점현황 조회</title>
""" + BASE_STYLE + """
</head><body><div class="wrap">
  <h1>🔎 창신리빙 입점현황 조회</h1>
  <p class="sub">비밀번호를 입력하면 시작할 수 있어요.</p>
  <div class="card">
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="post">
      <label>비밀번호</label>
      <input type="password" name="password" autofocus required>
      <button type="submit">들어가기</button>
    </form>
  </div>
</div></body></html>
"""

SEARCH_HTML = """
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>창신리빙 입점현황 조회</title>
""" + BASE_STYLE + """
</head><body><div class="wrap">
  <div class="logout"><a href="{{ url_for('logout') }}">로그아웃</a></div>
  <h1>🔎 창신리빙 입점현황 조회</h1>
  <p class="sub">품목코드나 상품명을 입력하세요. 여러 개는 줄을 바꿔서 입력하면 한 번에 검색돼요.</p>

  <div class="card">
    <form method="post" action="{{ url_for('search') }}">
      <label>품목코드 또는 상품명</label>
      <textarea name="keywords" placeholder="예) CSN-GBL040873" autofocus required>{{ raw_input or '' }}</textarea>
      <button type="submit">검색</button>
    </form>
    <p class="muted">지금 검색되는 채널: {{ configured_str }}</p>
  </div>

  {% if results_by_keyword %}
    {% for keyword, results, errors in results_by_keyword %}
      <div class="card">
        <div class="code-title">"{{ keyword }}"</div>
        {% if results %}
          <table>
            <tr><th>채널</th><th>상품명</th><th>상태</th><th>코드</th></tr>
            {% for r in results %}
              <tr>
                <td><span class="badge badge-ok">{{ r.platform }}</span></td>
                <td>{{ r.product_name or '-' }}</td>
                <td>{{ r.status or '-' }}</td>
                <td>{{ r.product_id or '-' }}</td>
              </tr>
            {% endfor %}
          </table>
        {% else %}
          <p class="muted">지금 검색 가능한 채널에서는 찾지 못했어요.</p>
        {% endif %}
        {% if errors %}
          <p class="muted">확인 안 된 채널: {{ errors|join(' / ') }}</p>
        {% endif %}
      </div>
    {% endfor %}
  {% endif %}

  <p class="footer-note">
    이 화면에서 검색되는 채널은 현재 열쇠(API 키)가 등록된 채널만이에요.
    나머지 채널은 회사에서 관리하는 "수기확인 체크리스트" 엑셀을 참고해주세요.
  </p>
</div></body></html>
"""


def _require_login():
    return session.get("authed") is True


@app.route("/login", methods=["GET", "POST"])
def login():
    if not SITE_PASSWORD:
        return (
            "관리자에게 알려주세요: 사이트 비밀번호(SITE_PASSWORD)가 아직 설정되지 않았어요.",
            500,
        )
    error = None
    if request.method == "POST":
        if request.form.get("password") == SITE_PASSWORD:
            session.permanent = True
            session["authed"] = True
            return redirect(url_for("index"))
        error = "비밀번호가 맞지 않아요. 다시 입력해주세요."
    return render_template_string(LOGIN_HTML, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    if not _require_login():
        return redirect(url_for("login"))
    configured = configured_platforms()
    configured_str = ", ".join(configured) if configured else "아직 없음 (관리자가 열쇠를 등록해야 해요)"
    return render_template_string(
        SEARCH_HTML, results_by_keyword=None, raw_input=None, configured_str=configured_str
    )


@app.route("/search", methods=["POST"])
def search():
    if not _require_login():
        return redirect(url_for("login"))

    raw_input = request.form.get("keywords", "")
    keywords = [line.strip() for line in raw_input.splitlines() if line.strip()]

    results_by_keyword = []
    for kw in keywords[:20]:  # 한 번에 너무 많이 넣으면 시간이 오래 걸려서 20개로 제한
        results, errors = run_search(kw)
        results_by_keyword.append((kw, results, errors))

    configured = configured_platforms()
    configured_str = ", ".join(configured) if configured else "아직 없음 (관리자가 열쇠를 등록해야 해요)"
    return render_template_string(
        SEARCH_HTML,
        results_by_keyword=results_by_keyword,
        raw_input=raw_input,
        configured_str=configured_str,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
