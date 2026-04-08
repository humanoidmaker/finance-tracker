from fastapi import APIRouter, Depends
from bson import ObjectId
from app.core.database import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/accounts", tags=["accounts"])

def s(doc):
    if doc: doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/")
async def list_accounts(db=Depends(get_db), user=Depends(get_current_user)):
    return {"success": True, "accounts": [s(d) for d in await db.accounts.find({"user_id": user["id"]}).to_list(20)]}

@router.get("/balances")
async def balances(db=Depends(get_db), user=Depends(get_current_user)):
    accts = await db.accounts.find({"user_id": user["id"]}).to_list(20)
    total = sum(a.get("balance", 0) for a in accts)
    return {"success": True, "accounts": [s(a) for a in accts], "total_balance": total}

@router.post("/")
async def create(data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data["user_id"] = user["id"]
    data.setdefault("balance", 0)
    r = await db.accounts.insert_one(data)
    return {"success": True, "id": str(r.inserted_id)}

@router.put("/{aid}")
async def update(aid: str, data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data.pop("id", None); data.pop("_id", None)
    await db.accounts.update_one({"_id": ObjectId(aid)}, {"$set": data})
    return {"success": True}
