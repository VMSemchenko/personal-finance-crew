"""
Load transactions.csv into SQLite database for efficient querying.
"""
import csv
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent
CSV_PATH = DATA_DIR / "transactions.csv"
DB_PATH = DATA_DIR / "finance.db"


def init_db() -> None:
    """Create SQLite database from transactions CSV."""
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            merchant TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            category TEXT NOT NULL,
            account TEXT NOT NULL,
            recurring INTEGER NOT NULL,
            weekday INTEGER,
            hour INTEGER,
            is_weekend INTEGER
        )
    """)

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            from datetime import datetime
            dt = datetime.fromisoformat(row["date"])
            rows.append((
                row["date"],
                row["merchant"],
                float(row["amount"]),
                row["currency"],
                row["category"],
                row["account"],
                1 if row["recurring"] == "True" else 0,
                dt.weekday(),  # 0=Mon..6=Sun
                dt.hour,
                1 if dt.weekday() >= 5 else 0,
            ))

    cur.executemany(
        "INSERT INTO transactions (date, merchant, amount, currency, category, account, recurring, weekday, hour, is_weekend) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )

    # Create useful indexes
    cur.execute("CREATE INDEX idx_category ON transactions(category)")
    cur.execute("CREATE INDEX idx_merchant ON transactions(merchant)")
    cur.execute("CREATE INDEX idx_date ON transactions(date)")
    cur.execute("CREATE INDEX idx_account ON transactions(account)")
    cur.execute("CREATE INDEX idx_recurring ON transactions(recurring)")

    # Create monthly summary view
    cur.execute("""
        CREATE VIEW monthly_summary AS
        SELECT
            substr(date, 1, 7) AS month,
            category,
            COUNT(*) AS tx_count,
            ROUND(SUM(amount), 2) AS total,
            ROUND(AVG(amount), 2) AS avg_amount
        FROM transactions
        GROUP BY substr(date, 1, 7), category
    """)

    conn.commit()
    print(f"Database created at {DB_PATH}")
    print(f"Loaded {len(rows)} transactions")

    # Verify
    cur.execute("SELECT COUNT(*) FROM transactions")
    count = cur.fetchone()[0]
    print(f"Verified: {count} rows in database")

    cur.execute("SELECT category, COUNT(*), ROUND(SUM(amount), 2) FROM transactions GROUP BY category ORDER BY SUM(amount)")
    print("\nBy category:")
    for cat, cnt, total in cur.fetchall():
        print(f"  {cat}: {cnt} txns, ${total:.2f}")

    conn.close()


if __name__ == "__main__":
    init_db()
