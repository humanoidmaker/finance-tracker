from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, timezone
from app.core.database import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

def s(doc):
    if doc: doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/")
async def list_txns(type: str = "", category: str = "", account: str = "", db=Depends(get_db), user=Depends(get_current_user)):
    f = {"user_id": user["id"]}
    if type: f["type"] = type
    if category: f["category"] = category
    if account: f["account_id"] = account
    return {"success": True, "transactions": [s(d) for d in await db.transactions.find(f).sort("date", -1).to_list(500)]}

@router.post("/")
async def create(data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data["user_id"] = user["id"]
    data["created_at"] = datetime.now(timezone.utc)
    r = await db.transactions.insert_one(data)
    # Update account balance
    if data.get("account_id"):
        inc = data["amount"] if data["type"] == "income" else -data["amount"]
        await db.accounts.update_one({"_id": ObjectId(data["account_id"])}, {"$inc": {"balance": inc}})
    return {"success": True, "id": str(r.inserted_id)}

@router.get("/summary")
async def summary(db=Depends(get_db), user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    pipe = [{"$match": {"user_id": user["id"], "date": {"$gte": start.isoformat()}}}, {"$group": {"_id": "$type", "total": {"$sum": "$amount"}}}]
    results = {r["_id"]: r["total"] for r in await db.transactions.aggregate(pipe).to_list(10)}
    return {"success": True, "summary": {"income": results.get("income", 0), "expense": results.get("expense", 0), "net": results.get("income", 0) - results.get("expense", 0)}}

@router.put("/{tid}")
async def update(tid: str, data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data.pop("id", None); data.pop("_id", None)
    await db.transactions.update_one({"_id": ObjectId(tid)}, {"$set": data})
    return {"success": True}

@router.delete("/{tid}")
async def delete(tid: str, user=Depends(get_current_user), db=Depends(get_db)):
    txn = await db.transactions.find_one({"_id": ObjectId(tid)})
    if txn and txn.get("account_id"):
        inc = -txn["amount"] if txn["type"] == "income" else txn["amount"]
        await db.accounts.update_one({"_id": ObjectId(txn["account_id"])}, {"$inc": {"balance": inc}})
    await db.transactions.delete_one({"_id": ObjectId(tid)})
    return {"success": True}
