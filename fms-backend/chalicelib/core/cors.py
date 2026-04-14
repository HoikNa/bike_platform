"""
cors.py — 전역 CORSConfig 팩토리

ALLOWED_ORIGIN 환경 변수 기준:
  미설정 (로컬)    → "*"  (모든 출처 허용)
  설정 (프로덕션)  → 지정된 Vercel 도메인만 허용

모든 Blueprint 라우트에서 cors=True 대신 cors=cors_config 를 사용하세요.
"""

import os
from chalice import CORSConfig

_origin: str = os.environ.get("ALLOWED_ORIGIN", "*")

cors_config = CORSConfig(
    allow_origin=_origin,
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
    expose_headers=["X-Request-ID"],
    allow_credentials=(_origin != "*"),   # 특정 오리진일 때만 credentials 허용
)
