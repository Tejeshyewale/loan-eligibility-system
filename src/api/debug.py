"""Temporary diagnostics: verify the real proxy-hop count on Render.

Gated by DEBUG_CLIENT_IP (default False). When the flag is off the endpoint
404s as if it never existed. DELETE THIS MODULE once the hop count is
confirmed in production.
"""
from fastapi import APIRouter, HTTPException, Request

from src.api.rate_limit import get_client_ip
from src.core import settings as settings_module

router = APIRouter(tags=["Diagnostics"])


@router.get("/_debug/client-ip")
def client_ip_debug(request: Request):
    if not settings_module.settings.DEBUG_CLIENT_IP:
        raise HTTPException(status_code=404, detail="Not found")
    peer = request.client.host if request.client is not None else None
    return {
        "x_forwarded_for": request.headers.get("x-forwarded-for"),
        "peer": peer,
        "trusted_proxy_hops": settings_module.settings.TRUSTED_PROXY_HOPS,
        "resolved_ip": get_client_ip(request),
    }
