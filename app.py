"""
AUB Mediterraneo Admissions - web front end for the INDE 513 project database.

Flask + SQLite. Every page reads from or writes to admissions.db.
Business rules are enforced by the database itself (CHECK constraints and
triggers in sql/01_schema.sql); the website only shows the error message
that the database returns, so a rule cannot be bypassed from the browser.

Run locally:   pip install -r requirements.txt
               python app.py            ->  http://127.0.0.1:5000
"""
import os
import re
import sqlite3
from datetime import date

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "admissions.db"))
CURRENT_CYCLE = 2027

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "inde513-aubmed-demo")


# ---------------------------------------------------------------- database
def build_database():
    """Create admissions.db from the SQL scripts (used on first start / Render)."""
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    for name in ("01_schema.sql", "02_data.sql"):
        with open(os.path.join(BASE_DIR, "sql", name), encoding="utf-8") as f:
            con.executescript(f.read())
    con.close()


def get_db():
    if "db" not in g:
        if not os.path.exists(DB_PATH):
            build_database()
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")   # required on every connection
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


def execute(statements):
    """Run one or more (sql, args) pairs in a single transaction.
    Returns None on success or the database error message."""
    db = get_db()
    try:
        with db:
            for sql, args in statements:
                db.execute(sql, args)
        return None
    except sqlite3.Error as e:
        return str(e)


def friendly(msg):
    """Turn raw SQLite messages into readable sentences."""
    if msg.startswith("UNIQUE constraint failed: Applicant.passportNo"):
        return "This passport number is already registered (BR24: no duplicate applicants)."
    if msg.startswith("UNIQUE constraint failed: Applicant.email"):
        return "This e-mail address is already used by another applicant."
    if msg.startswith("UNIQUE constraint failed: Application.applicantId"):
        return "BR3: this applicant already applied to this program in this cycle."
    if msg.startswith("UNIQUE constraint failed: Review"):
        return "BR16: this professor has already reviewed this application."
    if msg.startswith("CHECK constraint failed"):
        return "A value is outside its allowed range or list (" + msg.split(":", 1)[1].strip() + ")."
    return msg


@app.context_processor
def inject_globals():
    return {"current_cycle": CURRENT_CYCLE, "today": date.today().isoformat()}


# ---------------------------------------------------------------- dashboard
@app.route("/")
def dashboard():
    stats = {
        "applicants": query("SELECT COUNT(*) FROM Applicant", one=True)[0],
        "applications": query("SELECT COUNT(*) FROM Application", one=True)[0],
        "open": query("SELECT COUNT(*) FROM Application WHERE applicationStatus <> 'Decided'", one=True)[0],
        "pending_docs": query("SELECT COUNT(*) FROM ApplicationDocument d JOIN Application a "
                              "ON a.applicationId = d.applicationId WHERE a.applicationStatus <> 'Decided' "
                              "AND d.verificationStatus IN ('Pending','Mismatch')", one=True)[0],
        "accept_rate": query("SELECT ROUND(100.0*SUM(decisionType='Accepted')/COUNT(*),1) "
                             "FROM AdmissionDecision", one=True)[0],
        "avg_aid": query("SELECT ROUND(AVG(aidPercentage),1) FROM FinancialAidAward", one=True)[0],
    }
    per_program = query("""
        SELECT p.programId, p.programName, COUNT(a.applicationId) AS n,
               SUM(a.admissionYear = ?) AS current
        FROM Program p LEFT JOIN Application a ON a.programId = p.programId
        WHERE p.programStatus = 'Active'
        GROUP BY p.programId ORDER BY n DESC""", (CURRENT_CYCLE,))
    max_n = max([r["n"] for r in per_program] or [1]) or 1
    recent = query("""SELECT * FROM vw_ApplicationSummary
                      ORDER BY submissionDate DESC, applicationId DESC LIMIT 8""")
    decisions = query("""SELECT decisionType, COUNT(*) AS n FROM AdmissionDecision
                         GROUP BY decisionType ORDER BY n DESC""")
    return render_template("dashboard.html", stats=stats, per_program=per_program,
                           max_n=max_n, recent=recent, decisions=decisions)


# ---------------------------------------------------------------- applicants
@app.route("/applicants")
def applicants():
    q = request.args.get("q", "").strip()
    nat = request.args.get("nationality", "")
    sql = """SELECT v.*, (SELECT COUNT(*) FROM Application a WHERE a.applicantId = v.applicantId) AS apps
             FROM vw_ApplicantProfile v WHERE 1 = 1"""
    args = []
    if q:
        sql += " AND (v.fullName LIKE ? OR v.passportNo LIKE ? OR v.email LIKE ? OR CAST(v.applicantId AS TEXT) = ?)"
        args += [f"%{q}%"] * 3 + [q]
    if nat:
        sql += " AND EXISTS (SELECT 1 FROM ApplicantNationality n WHERE n.applicantId = v.applicantId AND n.nationality = ?)"
        args.append(nat)
    sql += " ORDER BY v.applicantId"
    rows = query(sql, args)
    nationalities = [r[0] for r in query("SELECT DISTINCT nationality FROM ApplicantNationality ORDER BY 1")]
    return render_template("applicants.html", rows=rows, q=q, nat=nat, nationalities=nationalities)


@app.route("/applicants/new", methods=["GET", "POST"])
def applicant_new():
    form = request.form
    if request.method == "POST":
        new_id = query("SELECT COALESCE(MAX(applicantId), 1000) + 1 FROM Applicant", one=True)[0]
        phones = [(form.get(f"phone{i}", "").strip(), form.get(f"phoneType{i}", "Mobile")) for i in (1, 2)]
        phones = [p for p in phones if p[0]]
        nats = [n.strip() for n in (form.get("nat1", ""), form.get("nat2", "")) if n.strip()]
        if not phones or not nats:
            flash("BR2: at least one phone number and one nationality are required.", "error")
            return render_template("applicant_form.html", form=form)
        stmts = [("""INSERT INTO Applicant (applicantId, passportNo, firstName, middleName, lastName,
                                             dateOfBirth, email) VALUES (?,?,?,?,?,?,?)""",
                  (new_id, form["passportNo"].strip().upper(), form["firstName"].strip(),
                   form.get("middleName", "").strip() or None, form["lastName"].strip(),
                   form["dateOfBirth"], form["email"].strip().lower()))]
        stmts += [("INSERT INTO ApplicantPhone VALUES (?,?,?)", (new_id, p, t)) for p, t in phones]
        stmts += [("INSERT INTO ApplicantNationality VALUES (?,?)", (new_id, n)) for n in dict.fromkeys(nats)]
        err = execute(stmts)
        if err:
            flash(friendly(err), "error")
            return render_template("applicant_form.html", form=form)
        flash(f"Applicant {new_id} was added.", "success")
        return redirect(url_for("applicant_detail", applicant_id=new_id))
    return render_template("applicant_form.html", form={})


@app.route("/applicants/<int:applicant_id>")
def applicant_detail(applicant_id):
    person = query("SELECT * FROM vw_ApplicantProfile WHERE applicantId = ?", (applicant_id,), one=True)
    if person is None:
        abort(404)
    raw = query("SELECT * FROM Applicant WHERE applicantId = ?", (applicant_id,), one=True)
    phones = query("SELECT * FROM ApplicantPhone WHERE applicantId = ?", (applicant_id,))
    nats = query("SELECT * FROM ApplicantNationality WHERE applicantId = ?", (applicant_id,))
    apps = query("SELECT * FROM vw_ApplicationSummary WHERE applicantId = ? ORDER BY admissionYear DESC",
                 (applicant_id,))
    return render_template("applicant_detail.html", p=person, raw=raw, phones=phones, nats=nats, apps=apps)


# ---------------------------------------------------------------- applications
@app.route("/applications")
def applications():
    f = {k: request.args.get(k, "") for k in ("year", "program", "status", "round")}
    sql, args = "SELECT * FROM vw_ApplicationSummary WHERE 1 = 1", []
    if f["year"]:
        sql += " AND admissionYear = ?"; args.append(int(f["year"]))
    if f["program"]:
        sql += " AND programId = ?"; args.append(f["program"])
    if f["status"]:
        sql += " AND applicationStatus = ?"; args.append(f["status"])
    if f["round"]:
        sql += " AND admissionRound = ?"; args.append(f["round"])
    sql += " ORDER BY admissionYear DESC, submissionDate DESC"
    rows = query(sql, args)
    programs = query("SELECT programId, programName FROM Program ORDER BY programName")
    years = [r[0] for r in query("SELECT admissionYear FROM AdmissionCycle ORDER BY 1 DESC")]
    return render_template("applications.html", rows=rows, f=f, programs=programs, years=years)


@app.route("/applications/new", methods=["GET", "POST"])
def application_new():
    applicants_list = query("SELECT applicantId, firstName || ' ' || lastName AS name FROM Applicant ORDER BY lastName")
    programs = query("SELECT programId, programName, degreeLevel FROM Program WHERE programStatus = 'Active' ORDER BY programName")
    cycles = query("SELECT * FROM AdmissionCycle ORDER BY admissionYear DESC")
    form = request.form if request.method == "POST" else {"applicantId": request.args.get("applicant", "")}
    if request.method == "POST":
        new_id = query("SELECT COALESCE(MAX(applicationId), 50000) + 1 FROM Application", one=True)[0]
        err = execute([("""INSERT INTO Application (applicationId, applicantId, programId, admissionYear,
                                                     submissionDate, admissionRound)
                           VALUES (?,?,?,?,?,?)""",
                        (new_id, int(form["applicantId"]), form["programId"], int(form["admissionYear"]),
                         form["submissionDate"], form["admissionRound"]))])
        if err:
            flash(friendly(err), "error")
        else:
            flash(f"Application {new_id} was submitted.", "success")
            return redirect(url_for("application_detail", application_id=new_id))
    return render_template("application_form.html", form=form, applicants=applicants_list,
                           programs=programs, cycles=cycles)


@app.route("/applications/<int:application_id>")
def application_detail(application_id):
    a = query("SELECT * FROM vw_ApplicationSummary WHERE applicationId = ?", (application_id,), one=True)
    if a is None:
        abort(404)
    docs = query("""SELECT d.*, r.requirementName, r.requirementType FROM ApplicationDocument d
                    JOIN Requirement r ON r.requirementId = d.requirementId
                    WHERE d.applicationId = ? ORDER BY d.documentNo""", (application_id,))
    checklist = query("""SELECT r.requirementId, r.requirementName, pr.isMandatory,
                                EXISTS (SELECT 1 FROM ApplicationDocument d WHERE d.applicationId = ?
                                        AND d.requirementId = r.requirementId) AS received
                         FROM ProgramRequirement pr JOIN Requirement r ON r.requirementId = pr.requirementId
                         WHERE pr.programId = ? ORDER BY pr.isMandatory DESC, r.requirementId""",
                      (application_id, a["programId"]))
    reviews = query("""SELECT r.*, p.firstName || ' ' || p.lastName AS professor FROM Review r
                       JOIN Professor p ON p.professorId = r.professorId
                       WHERE r.applicationId = ? ORDER BY r.reviewDate""", (application_id,))
    reviewers = query("""SELECT p.professorId, p.firstName || ' ' || p.lastName AS name FROM Professor p
                         JOIN Program pg ON pg.departmentId = p.departmentId
                         WHERE pg.programId = ? AND p.professorId NOT IN
                               (SELECT professorId FROM Review WHERE applicationId = ?)
                         ORDER BY p.lastName""", (a["programId"], application_id))
    requirements = query("SELECT requirementId, requirementName FROM Requirement ORDER BY requirementId")
    tuition = query("SELECT annualTuition FROM Program WHERE programId = ?", (a["programId"],), one=True)[0]
    award = query("SELECT * FROM FinancialAidAward WHERE applicationId = ?", (application_id,), one=True)
    return render_template("application_detail.html", a=a, docs=docs, checklist=checklist, reviews=reviews,
                           reviewers=reviewers, requirements=requirements, tuition=tuition, award=award)


@app.post("/applications/<int:application_id>/documents")
def add_document(application_id):
    n = query("SELECT COALESCE(MAX(documentNo), 0) + 1 FROM ApplicationDocument WHERE applicationId = ?",
              (application_id,), one=True)[0]
    fname = request.form.get("fileName", "").strip() or f"{application_id}_{request.form['requirementId'].lower()}.pdf"
    err = execute([("""INSERT INTO ApplicationDocument (applicationId, documentNo, requirementId, fileName, uploadDate)
                       VALUES (?,?,?,?,?)""",
                    (application_id, n, request.form["requirementId"], fname, request.form["uploadDate"]))])
    flash(friendly(err) if err else f"Document #{n} recorded (status: Pending).", "error" if err else "success")
    return redirect(url_for("application_detail", application_id=application_id) + "#documents")


@app.post("/applications/<int:application_id>/documents/<int:doc_no>/status")
def set_document_status(application_id, doc_no):
    status = request.form["status"]
    err = execute([("""UPDATE ApplicationDocument SET verificationStatus = ?
                       WHERE applicationId = ? AND documentNo = ?""", (status, application_id, doc_no))])
    flash(friendly(err) if err else f"Document #{doc_no} marked as {status}.", "error" if err else "success")
    back = request.form.get("next")
    if back == "verification":
        return redirect(url_for("verification"))
    return redirect(url_for("application_detail", application_id=application_id) + "#documents")


@app.post("/applications/<int:application_id>/reviews")
def add_review(application_id):
    err = execute([("""INSERT INTO Review (professorId, applicationId, score, reviewDate, comments)
                       VALUES (?,?,?,?,?)""",
                    (int(request.form["professorId"]), application_id, int(request.form["score"] or -1),
                     request.form["reviewDate"], request.form.get("comments", "").strip() or None))])
    flash(friendly(err) if err else "Review saved.", "error" if err else "success")
    return redirect(url_for("application_detail", application_id=application_id) + "#reviews")


@app.post("/applications/<int:application_id>/decision")
def add_decision(application_id):
    new_id = query("SELECT COALESCE(MAX(decisionId), 9000) + 1 FROM AdmissionDecision", one=True)[0]
    err = execute([("""INSERT INTO AdmissionDecision (decisionId, applicationId, decisionType, decisionDate)
                       VALUES (?,?,?,?)""",
                    (new_id, application_id, request.form["decisionType"], request.form["decisionDate"]))])
    flash(friendly(err) if err else "Decision recorded; the application is now Decided.", "error" if err else "success")
    return redirect(url_for("application_detail", application_id=application_id) + "#decision")


@app.post("/applications/<int:application_id>/aid")
def add_aid(application_id):
    new_id = query("SELECT COALESCE(MAX(awardId), 7000) + 1 FROM FinancialAidAward", one=True)[0]
    try:
        pct = float(request.form["aidPercentage"])
    except ValueError:
        pct = -1
    err = execute([("""INSERT INTO FinancialAidAward (awardId, applicationId, aidPercentage, awardType)
                       VALUES (?,?,?,?)""", (new_id, application_id, pct, request.form["awardType"]))])
    flash(friendly(err) if err else "Financial aid award saved.", "error" if err else "success")
    return redirect(url_for("application_detail", application_id=application_id) + "#decision")


# ---------------------------------------------------------------- verification queue
@app.route("/verification")
def verification():
    docs = query("""SELECT d.*, r.requirementName, a.programId, a.admissionYear,
                           ap.firstName || ' ' || ap.lastName AS applicant
                    FROM ApplicationDocument d
                    JOIN Application a  ON a.applicationId = d.applicationId
                    JOIN Applicant  ap  ON ap.applicantId  = a.applicantId
                    JOIN Requirement r  ON r.requirementId = d.requirementId
                    WHERE a.applicationStatus <> 'Decided'
                      AND d.verificationStatus IN ('Pending', 'Mismatch')
                    ORDER BY d.verificationStatus DESC, d.uploadDate, d.applicationId""")
    missing = query("""SELECT a.applicationId, ap.firstName || ' ' || ap.lastName AS applicant, a.programId,
                              r.requirementName
                       FROM Application a
                       JOIN Applicant ap ON ap.applicantId = a.applicantId
                       JOIN ProgramRequirement pr ON pr.programId = a.programId AND pr.isMandatory = 'Y'
                       JOIN Requirement r ON r.requirementId = pr.requirementId
                       WHERE a.applicationStatus <> 'Decided' AND r.requirementId <> 'RQ004'
                         AND NOT EXISTS (SELECT 1 FROM ApplicationDocument d
                                          WHERE d.applicationId = a.applicationId
                                            AND d.requirementId = pr.requirementId)
                       ORDER BY a.applicationId""")
    return render_template("verification.html", docs=docs, missing=missing)


# ---------------------------------------------------------------- programs
@app.route("/programs")
def programs():
    progs = query("""SELECT p.*, d.departmentName,
                            (SELECT COUNT(*) FROM Application a WHERE a.programId = p.programId) AS apps
                     FROM Program p JOIN Department d ON d.departmentId = p.departmentId
                     ORDER BY p.degreeLevel DESC, p.programName""")
    reqs = {}
    for r in query("""SELECT pr.programId, r.requirementName, pr.isMandatory FROM ProgramRequirement pr
                      JOIN Requirement r ON r.requirementId = pr.requirementId
                      ORDER BY pr.isMandatory DESC, r.requirementId"""):
        reqs.setdefault(r["programId"], []).append(r)
    profs = query("""SELECT p.*, d.departmentName, (SELECT COUNT(*) FROM Review r
                     WHERE r.professorId = p.professorId) AS reviews
                     FROM Professor p JOIN Department d ON d.departmentId = p.departmentId
                     ORDER BY p.departmentId, p.lastName""")
    return render_template("programs.html", progs=progs, reqs=reqs, profs=profs)


# ---------------------------------------------------------------- reports
def load_reports():
    """Reads sql/03_queries.sql so the website and the report use the same SQL."""
    with open(os.path.join(BASE_DIR, "sql", "03_queries.sql"), encoding="utf-8") as f:
        text = f.read()
    reports = []
    for block in re.split(r"\n(?=-- Q\d+:)", text)[1:]:
        lines = block.strip().splitlines()
        comment = [l[2:].strip() for l in lines if l.startswith("--")]
        sql = "\n".join(l for l in lines if not l.startswith("--")).strip()
        m = re.match(r"(Q\d+):\s*(.*)", comment[0])
        reports.append({"id": m.group(1), "title": " ".join([m.group(2)] + comment[1:]), "sql": sql})
    return reports


@app.route("/reports")
@app.route("/reports/<rid>")
def reports(rid=None):
    all_reports = load_reports()
    current = next((r for r in all_reports if r["id"] == rid), all_reports[0])
    cur = get_db().execute(current["sql"])
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return render_template("reports.html", reports=all_reports, current=current, cols=cols, rows=rows)


@app.errorhandler(404)
def not_found(_e):
    return render_template("base.html", not_found=True), 404


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
