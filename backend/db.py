import json
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent / "app.db"

_db = None


async def get_db():
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
    return _db


async def init_db():
    db = await get_db()

    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            resource_group TEXT,
            resources_scanned INTEGER,
            issues_found INTEGER,
            estimated_savings TEXT,
            analysis_result TEXT,
            status TEXT DEFAULT 'completed',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    await db.commit()


async def create_user(email, password_hash):
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO users(email, password_hash) VALUES(?, ?) RETURNING id",
        (email, password_hash)
    )
    row = await cursor.fetchone()
    await db.commit()
    return row["id"]


async def get_user_by_email(email):
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def save_analysis(
    user_id,
    resource_group,
    resources_scanned,
    issues_found,
    estimated_savings,
    analysis_result,
    status="completed"
):
    db = await get_db()
    cursor = await db.execute(
        """
        INSERT INTO analyses(
            user_id, resource_group, resources_scanned,
            issues_found, estimated_savings, analysis_result, status
        ) VALUES(?, ?, ?, ?, ?, ?, ?) RETURNING id
        """,
        (
            user_id,
            resource_group,
            resources_scanned,
            issues_found,
            str(estimated_savings),
            json.dumps(analysis_result),  # Store as JSON string
            status
        )
    )
    row = await cursor.fetchone()
    await db.commit()
    return row["id"]


async def get_history(user_id):
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    rows = await cursor.fetchall()
    results = []
    for r in rows:
        item = dict(r)
        # Deserialise JSON string back to object so frontend gets real object
        if isinstance(item.get("analysis_result"), str):
            try:
                item["analysis_result"] = json.loads(item["analysis_result"])
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(item)
    return results
