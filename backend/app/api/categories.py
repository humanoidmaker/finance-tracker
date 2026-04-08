from fastapi import APIRouter, Depends
from bson import ObjectId
from app.core.database import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/categories", tags=["categories"])

def s(doc):
    if doc: doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/")
async def list_cats(db=Depends(get_db), user=Depends(get_current_user)):
    return {"success": True, "categories": [s(d) for d in await db.categories.find().sort("type", 1).to_list(100)]}

@router.post("/")
async def create(data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data["slug"] = data["name"].lower().replace(" ", "-")
    r = await db.categories.insert_one(data)
    return {"success": True, "id": str(r.inserted_id)}

@router.put("/{cid}")
async def update(cid: str, data: dict, user=Depends(get_current_user), db=Depends(get_db)):
    data.pop("id", None); data.pop("_id", None)
    await db.categories.update_one({"_id": ObjectId(cid)}, {"$set": data})
    return {"success": True}

@router.delete("/{cid}")
async def delete(cid: str, user=Depends(get_current_user), db=Depends(get_db)):
    await db.categories.delete_one({"_id": ObjectId(cid)})
    return {"success": True}
