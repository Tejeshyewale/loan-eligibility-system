"""Single shared slowapi limiter (one in-memory store for all routes).

Client IP resolution: proxies APPEND the address they see to
X-Forwarded-For, so the chain looks like
``<client-supplied...>, <real-client-ip>`` (leftmost entries are fully
client-controlled). We therefore trust the Nth entry from the RIGHT, where
N = TRUSTED_PROXY_HOPS (default 1 = our edge proxy, e.g. Render).
If the header is missing or shorter than N, fall back to the connection
peer. TRUSTED_PROXY_HOPS = 0 is explicit direct-serve mode: XFF is ignored
completely and the peer address is always used (set this for local dev
without a proxy). render.yaml passes --proxy-headers to uvicorn so the
framework agrees on scheme/host behind the same proxy.
"""
from slowapi import Limiter
from starlette.requests import Request

from src.core import settings as settings_module


def _hops() -> int:
    return int(settings_module.settings.TRUSTED_PROXY_HOPS)


def _peer(request: Request) -> str:
    if request.client is not None:
        return request.client.host
    return "unknown"


def get_client_ip(request: Request) -> str:
    hops = _hops()
    if hops <= 0:
        return _peer(request)
    forwarded = request.headers.get("x-forwarded-for", "")
    chain = [part.strip() for part in forwarded.split(",") if part.strip()]
    if len(chain) >= hops:
        return chain[-hops]
    return _peer(request)


limiter = Limiter(key_func=get_client_ip)
