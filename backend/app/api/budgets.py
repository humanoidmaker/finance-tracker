from fastapi import APIRouter, Depends
from bson import ObjectId
from app.core.database import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/budgets", tags=["budgets"])

def s(doc):
    if doc: doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/")
async def list_budgets(month: str = "", db=Depends(get_db), user=Depends(get_current_user)):
    f = {"user_id": user["id"]}
    if month: f["month"] = month
    return {"success": True, "budgets": [s(d) for d in await db.budgets.find(f).to_list(50)]}

@router.get("/status")
async def budget_status(month: str = "", db=Depends(get_db), user=Depends(get_current_user)):
    from datetime import datetime
    if not month: month = datetime.now().strftime("%Y-%m")
    budgets = await db.budgets.find({"user_id": user["id"], "month": month}).to_list(50)
    result = []
    for b in budgets:
        # Calculate spent for this category this month
        start = f"{month}-01"
        end = f"{month}-31"
        pipe = [{"$match": {"user_id": user["id"], "type": "expense", "category": b.get("category_name", ""), "date": {"$gte": start, "$lte": end}}}, {"$group": {"_id": None, "spent": {"$sum": "$amount"}}}]
        r = await db.transactions.aggregate(pipe).to_list(1)
        spent = r[0]["spent"] if r else 0
        result.append({"category": b.get("category_name", ""), "budgeted": b["amount"], "spent": spent, "remaining": b["amount"] - spent, "percent": round(spent / b["amount"] * 100) if b["amount"] > 0 else 0})
    return {"success": True, "status": result}

@router.post("/")
async def create(data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data["user_id"] = user["id"]
    r = await db.budgets.insert_one(data)
    return {"success": True, "id": str(r.inserted_id)}

@router.put("/{bid}")
async def update(bid: str, data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data.pop("id", None); data.pop("_id", None)
    await db.budgets.update_one({"_id": ObjectId(bid)}, {"$set": data})
    return {"success": True}
