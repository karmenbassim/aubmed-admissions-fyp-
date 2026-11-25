# AUB Mediterraneo Admissions Database — INDE 513 Project

SQLite database and Flask website for the admissions process at AUB Mediterraneo
(INDE 513 Information Systems, Dr. Maysaa Jaafar).

Website link: ______________________ (add after deploying on Render)

## Folder contents

| Path | Content |
|---|---|
| `sql/01_schema.sql` | CREATE TABLE statements (14 tables), indexes, 10 triggers, 2 views |
| `sql/02_data.sql` | INSERT statements — 731 fictional sample records |
| `sql/03_queries.sql` | The 13 queries of Chapter 7 |
| `sql/04_constraint_tests.sql` | 12 invalid statements that the database must reject |
| `admissions.db` | Ready-built SQLite database (same content as the scripts) |
| `app.py`, `templates/`, `static/` | Flask website |
| `tools/build_db.py` | Rebuilds `admissions.db` from the SQL scripts |
| `tools/run_tests.py` | Runs the constraint tests and prints why each statement is rejected |
| `tools/generate_data.py` | Script used to generate the fictional sample data |
| `diagrams/` | Full-size ER diagram, relational schema and FD diagrams |
| `requirements.txt`, `render.yaml` | Python packages and Render deployment settings |

## 1. Run the SQL with the sqlite3 shell

```bash
sqlite3 admissions.db < sql/01_schema.sql
sqlite3 admissions.db < sql/02_data.sql
sqlite3 -box admissions.db < sql/03_queries.sql
```

Each script begins with `PRAGMA foreign_keys = ON;`. The statements in
`04_constraint_tests.sql` are meant to fail; run them one by one, or run
`python tools/run_tests.py` to see all 12 rejections at once.
DB Browser for SQLite can also open `admissions.db` directly.

## 2. Run the website locally

Requires Python 3.10 or later.

```bash
pip install -r requirements.txt
python tools/build_db.py      # optional: resets the database to the sample data
python app.py
```

Open http://127.0.0.1:5000 in a browser.

If `admissions.db` is missing, the website builds it automatically from the SQL scripts.

## 3. Put the website online (Render, free plan)

1. Create a GitHub repository and upload the contents of this folder.
2. On https://render.com choose **New → Blueprint** (or **Web Service**) and select the repository.
3. Render reads `render.yaml`:
   - build command: `pip install -r requirements.txt && python tools/build_db.py`
   - start command: `gunicorn app:app`
4. When the deploy finishes, copy the `.onrender.com` link into the report and this README.

On the free plan the disk is reset on every deploy, so records added online go back to the
sample data after a redeploy. This is fine for a demo.

## Notes

- All people, passport numbers, e-mails and phone numbers in the sample data are invented.
- Tuition amounts and the department grouping are illustrative assumptions.
- Business rules are enforced by the database (CHECK constraints and triggers). The website
  shows the database's error message when a rule is broken.
- Fonts: Open Sans and Crimson Text (SIL Open Font License, included in `static/fonts`).
