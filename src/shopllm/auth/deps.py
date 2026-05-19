"""FastAPI dependency: authenticate a request via Bearer API key."""
from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from shopllm.auth.api_keys import hash_api_key
from shopllm.db.models import ApiKey, Tenant
from shopllm.db.session import SessionLocal

_bearer = HTTPBearer()


async def authenticate(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> Tenant:
    h = hash_api_key(credentials.credentials)
    async with SessionLocal() as s:
        result = await s.execute(select(ApiKey).where(ApiKey.key_hash == h))
        api_key = result.scalar_one_or_none()
        if api_key is None:
            raise HTTPException(status_code=401, detail="Invalid API key.")
        tenant = await s.get(Tenant, api_key.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=401, detail="Tenant not found.")
    return tenant
