"""Builds admissions.db from the SQL scripts.

Usage:  python tools/build_db.py            (creates ./admissions.db)
"""
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "admissions.db")


def build(db_path=DB):
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    for name in ("01_schema.sql", "02_data.sql"):
        with open(os.path.join(ROOT, "sql", name), encoding="utf-8") as f:
            con.executescript(f.read())
    problems = con.execute("PRAGMA foreign_key_check").fetchall()
    con.close()
    if problems:
        sys.exit(f"Foreign key problems: {problems}")
    print(f"Database created: {db_path}")


if __name__ == "__main__":
    build()
