"""Persistent SQLite database manager for XeroxAI 2.0.

Provides schemas, seeding, and CRUD operations for counter print orders and
customizable shop pricing rate cards with transactional reliability.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

DB_PATH: str = os.getenv(
    "SQLITE_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "xeroxai.db"),
)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a new SQLite connection configured with Row factory and busy timeout.

    Args:
        db_path: Optional filesystem path to SQLite database. Defaults to DB_PATH.

    Returns:
        Configured sqlite3.Connection instance.
    """
    path = db_path or DB_PATH
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes SQLite tables and default pricing configuration if not present.

    Args:
        db_path: Optional filesystem path to SQLite database. Defaults to DB_PATH.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Pricing Configuration Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pricing_config (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        bw_single REAL NOT NULL DEFAULT 2.0,
        bw_double REAL NOT NULL DEFAULT 3.0,
        color_single REAL NOT NULL DEFAULT 10.0,
        color_double REAL NOT NULL DEFAULT 16.0,
        a3_multiplier REAL NOT NULL DEFAULT 2.0,
        legal_multiplier REAL NOT NULL DEFAULT 1.25,
        letter_multiplier REAL NOT NULL DEFAULT 1.0,
        lamination_a4 REAL NOT NULL DEFAULT 20.0,
        lamination_a3 REAL NOT NULL DEFAULT 40.0,
        updated_at TEXT NOT NULL
    )
    """)

    # Seed default rates if table is empty
    cursor.execute("SELECT id FROM pricing_config WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute(
            """
        INSERT INTO pricing_config (
            id, bw_single, bw_double, color_single, color_double,
            a3_multiplier, legal_multiplier, letter_multiplier,
            lamination_a4, lamination_a3, updated_at
        ) VALUES (1, 2.0, 3.0, 10.0, 16.0, 2.0, 1.25, 1.0, 20.0, 40.0, ?)
        """,
            (datetime.now(timezone.utc).isoformat(),),
        )
        logger.info("Seeded default pricing configuration into database.")

    # 2. Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT DEFAULT '',
        items_json TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        notes TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # Indices for high-frequency counter queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC)"
    )

    conn.commit()
    conn.close()


def get_pricing_config(db_path: Optional[str] = None) -> dict[str, Any]:
    """Retrieves the current active shop pricing configuration.

    Args:
        db_path: Optional filesystem path to SQLite database. Defaults to DB_PATH.

    Returns:
        Dictionary mapping pricing rate keys to their numeric amounts and update timestamp.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pricing_config WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)

    return {
        "bw_single": 2.0,
        "bw_double": 3.0,
        "color_single": 10.0,
        "color_double": 16.0,
        "a3_multiplier": 2.0,
        "legal_multiplier": 1.25,
        "letter_multiplier": 1.0,
        "lamination_a4": 20.0,
        "lamination_a3": 40.0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def update_pricing_config(
    new_config: dict[str, float], db_path: Optional[str] = None
) -> dict[str, Any]:
    """Updates shop rates in the persistent database.

    Args:
        new_config: Dictionary containing updated pricing parameters.
        db_path: Optional filesystem path to SQLite database. Defaults to DB_PATH.

    Returns:
        Updated pricing configuration dictionary.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
    UPDATE pricing_config SET
        bw_single = :bw_single,
        bw_double = :bw_double,
        color_single = :color_single,
        color_double = :color_double,
        a3_multiplier = :a3_multiplier,
        legal_multiplier = :legal_multiplier,
        letter_multiplier = :letter_multiplier,
        lamination_a4 = :lamination_a4,
        lamination_a3 = :lamination_a3,
        updated_at = :updated_at
    WHERE id = 1
    """,
        {
            "bw_single": float(new_config.get("bw_single", 2.0)),
            "bw_double": float(new_config.get("bw_double", 3.0)),
            "color_single": float(new_config.get("color_single", 10.0)),
            "color_double": float(new_config.get("color_double", 16.0)),
            "a3_multiplier": float(new_config.get("a3_multiplier", 2.0)),
            "legal_multiplier": float(new_config.get("legal_multiplier", 1.25)),
            "letter_multiplier": float(new_config.get("letter_multiplier", 1.0)),
            "lamination_a4": float(new_config.get("lamination_a4", 20.0)),
            "lamination_a3": float(new_config.get("lamination_a3", 40.0)),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    conn.commit()
    conn.close()
    return get_pricing_config(db_path)


def generate_order_id(conn: sqlite3.Connection) -> str:
    """Generates a sequential daily counter order identifier.

    Format: XRX-YYYYMMDD-XXXX (e.g., XRX-20261119-0001).

    Args:
        conn: Open SQLite database connection.

    Returns:
        Formatted unique order identifier string.
    """
    date_str = datetime.now().strftime("%Y%m%d")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT count(*) as cnt FROM orders WHERE order_id LIKE ?",
        (f"XRX-{date_str}-%",),
    )
    cnt = cursor.fetchone()["cnt"] + 1
    return f"XRX-{date_str}-{cnt:04d}"


def create_order(
    customer_name: str,
    items: list[dict[str, Any]],
    total_amount: float,
    customer_phone: str = "",
    notes: str = "",
    status: str = "Pending",
    db_path: Optional[str] = None,
) -> dict[str, Any]:
    """Creates and persists a new counter order record.

    Args:
        customer_name: Full name of the customer placing the order.
        items: List of line-item calculation dictionaries.
        total_amount: Grand total billing amount in INR.
        customer_phone: Optional phone contact string.
        notes: Optional operator or customer instructions.
        status: Lifecycle status ('Pending', 'Processing', 'Completed').
        db_path: Optional database file path.

    Returns:
        Full order dictionary including deserialized items and order_id.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    order_id = generate_order_id(conn)
    now = datetime.now(timezone.utc).isoformat()
    items_json = json.dumps(items)

    cursor.execute(
        """
    INSERT INTO orders (
        order_id, customer_name, customer_phone, items_json,
        total_amount, status, notes, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            order_id,
            customer_name,
            customer_phone,
            items_json,
            total_amount,
            status,
            notes,
            now,
            now,
        ),
    )
    conn.commit()

    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = dict(cursor.fetchone())
    row["items"] = json.loads(row["items_json"])
    conn.close()
    return row


def get_order_by_id(
    order_id: str, db_path: Optional[str] = None
) -> Optional[dict[str, Any]]:
    """Retrieves a single order by its public business identifier.

    Args:
        order_id: Unique order identifier string (e.g., 'XRX-20261119-0001').
        db_path: Optional database file path.

    Returns:
        Order dictionary with deserialized line items, or None if not found.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    data = dict(row)
    data["items"] = json.loads(data["items_json"])
    return data


def list_orders(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    db_path: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Lists orders with optional status filtering, search term matching, and limit.

    Args:
        status: Optional status filter ('Pending', 'Processing', 'Completed', or 'All').
        search: Optional search term matching customer name, phone, or order_id.
        limit: Maximum number of records to return (default 50).
        db_path: Optional database file path.

    Returns:
        List of order dictionaries sorted by most recent first.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM orders WHERE 1=1"
    params: list[Any] = []

    if status and status.lower() != "all":
        query += " AND status = ?"
        params.append(status)

    if search:
        query += " AND (customer_name LIKE ? OR customer_phone LIKE ? OR order_id LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        d["items"] = json.loads(d["items_json"])
        results.append(d)
    return results


def update_order_status(
    order_id: str, new_status: str, db_path: Optional[str] = None
) -> Optional[dict[str, Any]]:
    """Updates the lifecycle status of an existing order.

    Args:
        order_id: Unique order identifier string.
        new_status: New status ('Pending', 'Processing', or 'Completed').
        db_path: Optional database file path.

    Returns:
        Updated order dictionary, or None if the order does not exist.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        """
    UPDATE orders SET status = ?, updated_at = ? WHERE order_id = ?
    """,
        (new_status, now, order_id),
    )
    conn.commit()

    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    d = dict(row)
    d["items"] = json.loads(d["items_json"])
    return d
