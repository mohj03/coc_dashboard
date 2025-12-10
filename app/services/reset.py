import sqlite3

DB_PATH = "/home/ubuntu/uguwewe/data/sql_db/cw_history.db"

def reset_database():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        # Hent alle tabeller (unntatt interne)
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [t[0] for t in c.fetchall()]

        # Tøm hver tabell
        for table in tables:
            c.execute(f"DELETE FROM {table};")
            print(f"Tømt tabell: {table}")

        conn.commit()
    print("✅ cw_history nullstilt (alle data slettet, struktur beholdt).")
