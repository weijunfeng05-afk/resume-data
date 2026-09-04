import json
import os
import sys

import httpx


BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
MODEL = os.getenv("ARK_MODEL", "doubao-seed-2-0-lite-260215")
API_KEY = os.getenv("ARK_API_KEY", "")


def main() -> int:
    if "/api/coding/" in BASE_URL:
        print("CONFIG_ERROR=ARK_BASE_URL must not contain /api/coding/v3")
        return 2
    if not API_KEY:
        print("CONFIG_ERROR=ARK_API_KEY is missing; no authenticated request was sent")
        return 2

    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "只回复：连接成功"}],
        "max_tokens": 16,
        "temperature": 0,
    }
    try:
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            content=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=30,
        )
    except httpx.HTTPError as exc:
        print("HTTP_STATUS=NO_RESPONSE")
        print(f"RESPONSE_BODY={exc}")
        return 1

    print(f"HTTP_STATUS={response.status_code}")
    print(f"RESPONSE_BODY={response.text}")
    return 0 if response.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
