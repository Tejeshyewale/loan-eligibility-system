"""Single shared slowapi limiter (one in-memory store for all routes).

Client IP resolution: proxies APPEND the address they see to
X-Forwarded-For, so the chain looks like
``<client-supplied...>, <real-client-ip>`` (leftmost entries are fully
client-controlled). We therefore trust the Nth entry from the RIGHT, where
N = TRUSTED_PROXY_HOPS (default 1 = our edge proxy, e.g. Render).
If the header is missing or shorter than N, fall back to the connection
peer. render.yaml passes --proxy-headers to uvicorn so the framework
agrees on scheme/host behind the same proxy.
"""
from slowapi import Limiter
from starlette.requests import Request

from src.core.settings import TRUSTED_PROXY_HOPS


def get_client_ip(request: Request) -> str:
    hops = max(1, int(TRUSTED_PROXY_HOPS or 1))
    forwarded = request.headers.get("x-forwarded-for", "")
    chain = [part.strip() for part in forwarded.split(",") if part.strip()]
    if len(chain) >= hops:
        return chain[-hops]
    if request.client is not None:
        return request.client.host
    return "unknown"


limiter = Limiter(key_func=get_client_ip)
