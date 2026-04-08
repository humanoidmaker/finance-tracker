import asyncio, sys, random
from datetime import datetime, timezone, timedelta
sys.path.insert(0, ".")
from app.core.database import init_db, get_db

async def seed():
    await init_db()
    db = await get_db()
    if await db.transactions.count_documents({}) > 0:
        print("Data exists"); return

    admin = await db.users.find_one({"role": "admin"})
    uid = str(admin["_id"]) if admin else "system"

    # Categories
    income_cats = [("Salary", "income"), ("Freelance", "income"), ("Investment", "income"), ("Other Income", "income")]
    expense_cats = [("Food", "expense"), ("Transport", "expense"), ("Shopping", "expense"), ("Bills", "expense"), ("Entertainment", "expense"), ("Health", "expense"), ("Education", "expense"), ("Rent", "expense"), ("EMI", "expense")]
    for name, typ in income_cats + expense_cats:
        await db.categories.insert_one({"name": name, "slug": name.lower().replace(" ", "-"), "type": typ})

    # Accounts
    savings_id = (await db.accounts.insert_one({"name": "Savings Account", "type": "savings", "balance": 50000, "user_id": uid})).inserted_id
    cash_id = (await db.accounts.insert_one({"name": "Cash", "type": "cash", "balance": 5000, "user_id": uid})).inserted_id
    current_id = (await db.accounts.insert_one({"name": "Current Account", "type": "current", "balance": 25000, "user_id": uid})).inserted_id
    acct_ids = [str(savings_id), str(cash_id), str(current_id)]

    now = datetime.now(timezone.utc)
    # Generate 60 transactions over 30 days
    for i in range(60):
        day = random.randint(0, 29)
        date = (now - timedelta(days=day)).strftime("%Y-%m-%d")
        if i < 2:  # Salary on 1st
            await db.transactions.insert_one({"type": "income", "amount": 50000, "category": "Salary", "account_id": acct_ids[0], "date": f"{now.strftime('%Y-%m')}-01", "description": "Monthly salary", "user_id": uid, "created_at": now - timedelta(days=day)})
        elif i < 4:  # Rent on 5th
            await db.transactions.insert_one({"type": "expense", "amount": 15000, "category": "Rent", "account_id": acct_ids[0], "date": f"{now.strftime('%Y-%m')}-05", "description": "Monthly rent", "user_id": uid, "created_at": now - timedelta(days=day)})
        elif i < 10:  # Freelance
            await db.transactions.insert_one({"type": "income", "amount": random.randint(5000, 15000), "category": "Freelance", "account_id": random.choice(acct_ids[:2]), "date": date, "description": random.choice(["Web project", "Design work", "Consulting"]), "user_id": uid, "created_at": now - timedelta(days=day)})
        else:
            cat = random.choice(["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Education", "EMI"])
            amounts = {"Food": (100, 800), "Transport": (50, 500), "Shopping": (200, 3000), "Bills": (500, 3000), "Entertainment": (100, 1500), "Health": (200, 2000), "Education": (500, 5000), "EMI": (3000, 5000)}
            lo, hi = amounts.get(cat, (100, 1000))
            await db.transactions.insert_one({"type": "expense", "amount": random.randint(lo, hi), "category": cat, "account_id": random.choice(acct_ids), "date": date, "description": f"{cat} expense", "user_id": uid, "created_at": now - timedelta(days=day)})

    # Budgets for current month
    month = now.strftime("%Y-%m")
    for cat, amt in [("Food", 10000), ("Transport", 3000), ("Shopping", 5000), ("Bills", 8000), ("Entertainment", 2000)]:
        await db.budgets.insert_one({"category_name": cat, "month": month, "amount": amt, "user_id": uid})

    print("Seeded: categories, 3 accounts, 60 transactions, 5 budgets")

asyncio.run(seed())
