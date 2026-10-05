"""Single shared slowapi limiter (one in-memory store for all routes).

Client IP resolution honors X-Forwarded-For (first entry) so rate limits
apply per real client behind Render's reverse proxy (render.yaml passes
--proxy-headers to uvicorn). NOTE: only trustworthy behind a proxy that
sets/overwrites XFF — a direct client could spoof it. Falls back to the
connection peer when no forwarding header is present.
"""
from slowapi import Limiter
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    if request.client is not None:
        return request.client.host
    return "unknown"


limiter = Limiter(key_func=get_client_ip)
