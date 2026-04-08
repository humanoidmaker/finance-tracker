from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.api import auth, transactions, categories, accounts, budgets, settings as settings_api

@asynccontextmanager
async def lifespan(app):
    await init_db()
    yield

app = FastAPI(title="MoneyWise Finance API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(accounts.router)
app.include_router(budgets.router)
app.include_router(settings_api.router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "MoneyWise Finance"}

@app.get("/api/stats")
async def stats():
    from app.core.database import get_db as gdb
    db = await gdb()
    tc = await db.transactions.count_documents({})
    accts = await db.accounts.find().to_list(20)
    total_bal = sum(a.get("balance", 0) for a in accts)
    return {"stats": {"total_transactions": tc, "total_balance": total_bal, "accounts": len(accts)}}
