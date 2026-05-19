import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from shopllm.db.models import Base, Tenant, ApiKey
from shopllm.db.session import engine, SessionLocal
from shopllm.auth.api_keys import generate_api_key

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as s:
        t = Tenant(name="demo", plan="pro", monthly_budget_usd=50)
        s.add(t); await s.flush()
        full, prefix, h = generate_api_key()
        s.add(ApiKey(tenant_id=t.id, key_prefix=prefix, key_hash=h))
        await s.commit()
        print("Tenant:", t.id)
        print("API KEY (save it now!):", full)

asyncio.run(main())
