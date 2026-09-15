"""Single shared slowapi limiter (one in-memory store for all routes)."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
