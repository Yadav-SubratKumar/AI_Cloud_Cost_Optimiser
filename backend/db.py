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
            role TEXT NOT NULL DEFAULT 'finance_manager',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Safe migration for databases created by earlier project versions.
    columns = await db.execute_fetchall("PRAGMA table_info(users)")
    column_names = {row[1] for row in columns}
    if "role" not in column_names:
        await db.execute(
            "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'cloud_admin'"
        )

    await db.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            token_hash TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT,
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


async def create_user(email, password_hash, role="finance_manager"):
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO users(email, password_hash, role) VALUES(?, ?, ?) RETURNING id",
        (email, password_hash, role),
    )
    row = await cursor.fetchone()
    await db.commit()
    return row["id"]


async def get_user_by_email(email):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_user_by_id(user_id):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_user_role(user_id, role):
    db = await get_db()
    await db.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    await db.commit()


async def save_password_reset_token(user_id, token_hash, expires_at):
    db = await get_db()
    await db.execute(
        "UPDATE password_reset_tokens SET used_at = datetime('now') WHERE user_id = ? AND used_at IS NULL",
        (user_id,),
    )
    await db.execute(
        "INSERT INTO password_reset_tokens(user_id, token_hash, expires_at) VALUES(?, ?, ?)",
        (user_id, token_hash, expires_at),
    )
    await db.commit()


async def get_valid_password_reset_token(token_hash):
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT * FROM password_reset_tokens
        WHERE token_hash = ? AND used_at IS NULL AND expires_at > datetime('now')
        """,
        (token_hash,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def consume_password_reset_token(token_id):
    db = await get_db()
    await db.execute(
        "UPDATE password_reset_tokens SET used_at = datetime('now') WHERE id = ?",
        (token_id,),
    )
    await db.commit()


async def update_password(user_id, password_hash):
    db = await get_db()
    await db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (password_hash, user_id),
    )
    await db.commit()


async def save_analysis(user_id, resource_group, resources_scanned, issues_found,
                       estimated_savings, analysis_result, status="completed"):
    db = await get_db()
    cursor = await db.execute(
        """
        INSERT INTO analyses(
            user_id, resource_group, resources_scanned,
            issues_found, estimated_savings, analysis_result, status
        ) VALUES(?, ?, ?, ?, ?, ?, ?) RETURNING id
        """,
        (
            user_id, resource_group, resources_scanned, issues_found,
            str(estimated_savings), json.dumps(analysis_result), status,
        ),
    )
    row = await cursor.fetchone()
    await db.commit()
    return row["id"]


async def get_history(user_id, include_all=False):
    """Return a user's analyses, or all analyses for roles that review organisation-wide costs."""
    db = await get_db()
    if include_all:
        cursor = await db.execute(
            "SELECT * FROM analyses ORDER BY created_at DESC, id DESC"
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC, id DESC",
            (user_id,),
        )
    rows = await cursor.fetchall()
    results = []
    for r in rows:
        item = dict(r)
        if isinstance(item.get("analysis_result"), str):
            try:
                item["analysis_result"] = json.loads(item["analysis_result"])
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(item)
    return results


async def get_analysis(user_id, analysis_id, include_all=False):
    db = await get_db()
    if include_all:
        cursor = await db.execute(
            "SELECT * FROM analyses WHERE id = ?",
            (analysis_id,),
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id),
        )
    row = await cursor.fetchone()
    if not row:
        return None
    item = dict(row)
    if isinstance(item.get("analysis_result"), str):
        try:
            item["analysis_result"] = json.loads(item["analysis_result"])
        except (json.JSONDecodeError, TypeError):
            pass
    return item
