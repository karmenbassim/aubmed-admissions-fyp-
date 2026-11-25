"""Runs every statement of sql/04_constraint_tests.sql against a fresh copy
of the database and prints the error that stops it.

Usage:  python tools/run_tests.py
"""
import os
import re
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

con = sqlite3.connect(":memory:")
con.execute("PRAGMA foreign_keys = ON")
for name in ("01_schema.sql", "02_data.sql"):
    con.executescript(open(os.path.join(ROOT, "sql", name), encoding="utf-8").read())

text = open(os.path.join(ROOT, "sql", "04_constraint_tests.sql"), encoding="utf-8").read()
blocks = re.findall(r"-- (T\d+)\s+(.*?)\n(.*?;)", text, re.S)
passed = 0
for tid, title, sql in blocks:
    try:
        cur = con.execute(sql)
        result = f"NOT BLOCKED (rows affected: {cur.rowcount})"
    except sqlite3.Error as e:
        result = f"blocked -> {e}"
        passed += 1
    print(f"{tid:<4} {title.strip():<62} {result}")
print(f"\n{passed} of {len(blocks)} invalid statements were rejected by the database.")
