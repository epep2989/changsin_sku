"""
공통 헬퍼: 개발자 문서가 로그인/승인 뒤에만 열리는(=JS로 렌더링돼 이번 조사에서
자동으로 긁어올 수 없었던) 채널들을 위한 뼈대.

lotteon.py / ssg.py / interpark.py / cjonstyle.py / kakao.py / toss.py 는
"이 채널에 공식 Open API가 있다"는 사실은 확인됐지만, 정확한 엔드포인트/파라미터명은
실제 발급받은 계정으로 로그인해야 보이는 문서 안에 있어서 이번 조사로는 확인하지 못했습니다.

이 파일의 GatedPlatformError 를 사용해, "미구현"이 아니라 "왜 아직 완성할 수 없는지"를
명확하게 알려주도록 통일했습니다. 발급받은 후 실제 API 문서(또는 curl 예제)를 공유해주시면
해당 모듈만 완성해드릴 수 있습니다.
"""
from __future__ import annotations


class GatedPlatformError(NotImplementedError):
    pass


def not_yet_implemented(platform_name: str, portal_url: str, note: str = "") -> None:
    msg = (
        f"[{platform_name}] 공식 Open API가 있는 것은 확인됐지만, "
        f"정확한 엔드포인트/인증 파라미터는 승인된 계정으로 로그인해야 보이는 문서 안에 있어 "
        f"이번 조사로는 확인하지 못했습니다. {portal_url} 에서 API를 신청/발급받으신 뒤, "
        f"문서나 요청 예제(curl 등)를 공유해주시면 이어서 구현해드릴 수 있습니다."
    )
    if note:
        msg += f" 참고: {note}"
    raise GatedPlatformError(msg)
