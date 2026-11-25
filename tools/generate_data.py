"""Generates sql/02_data.sql with fictional but consistent sample data.

All people, passport numbers, e-mails and phone numbers are invented.
Fixed random seed -> the same file every time it is run.
"""
import random
from datetime import date, timedelta

random.seed(513)
out = []
def emit(s): out.append(s)
def q(v):
    if v is None: return "NULL"
    if isinstance(v, (int, float)): return str(v)
    return "'" + str(v).replace("'", "''") + "'"
def ins(table, cols, rows):
    emit(f"INSERT INTO {table} ({', '.join(cols)}) VALUES")
    emit(",\n".join("    (" + ", ".join(q(v) for v in r) + ")" for r in rows) + ";\n")

emit("""-- =====================================================================
--  AUB Mediterraneo Admissions Database
--  File 2 of 3: sample data (fictional people - no real personal data)
-- =====================================================================
PRAGMA foreign_keys = ON;
BEGIN TRANSACTION;
""")

departments = [
    ("CMPS", "Computer Science"),
    ("INDE", "Industrial Engineering and Management"),
    ("BUSN", "Business Administration"),
    ("HUSS", "Humanities and Social Sciences"),
]
emit("-- Departments (grouping of programs is an assumption of the team)")
ins("Department", ["departmentId", "departmentName"], departments)

programs = [
    ("UGCMP", "BS in Computer Science", "Undergraduate", "Active", 17500, "CMPS"),
    ("UGINE", "BS in Industrial Engineering", "Undergraduate", "Active", 17500, "INDE"),
    ("GREMG", "MS in Engineering Management", "Graduate", "Active", 19000, "INDE"),
    ("UGBMG", "BBA in Business Administration - Management", "Undergraduate", "Active", 16500, "BUSN"),
    ("UGBDM", "BBA in Business Administration - Digital Marketing", "Undergraduate", "Active", 16500, "BUSN"),
    ("GRBAN", "MS in Business Analytics", "Graduate", "Active", 19000, "BUSN"),
    ("UGPPE", "BA in Philosophy, Politics and Economics", "Undergraduate", "Active", 15500, "HUSS"),
    ("UGPSY", "BS in Psychology", "Undergraduate", "Active", 15500, "HUSS"),
    ("UGDSC", "BS in Data Science", "Undergraduate", "Planned", 17500, "CMPS"),
]
emit("-- Programs (annual tuition values are illustrative, in EUR)")
ins("Program", ["programId", "programName", "degreeLevel", "programStatus", "annualTuition", "departmentId"], programs)

professors = [
    (101, "Karim", "Haddad", "kh101@aubmed.example.cy", "CMPS"),
    (102, "Elena", "Christou", "ec102@aubmed.example.cy", "CMPS"),
    (103, "Omar", "Saleh", None, "CMPS"),
    (104, "Lina", "Fakhoury", "lf104@aubmed.example.cy", "INDE"),
    (105, "Andreas", "Georgiou", "ag105@aubmed.example.cy", "INDE"),
    (106, "Rana", "Khoury", "rk106@aubmed.example.cy", "INDE"),
    (107, "Nicolas", "Papadakis", "np107@aubmed.example.cy", "BUSN"),
    (108, "Maya", "Aoun", "ma108@aubmed.example.cy", "BUSN"),
    (109, "Fadi", "Mansour", None, "BUSN"),
    (110, "Sofia", "Ioannou", "si110@aubmed.example.cy", "BUSN"),
    (111, "Hadi", "Nasr", "hn111@aubmed.example.cy", "HUSS"),
    (112, "Katerina", "Demetriou", "kd112@aubmed.example.cy", "HUSS"),
    (113, "Jad", "Rizk", "jr113@aubmed.example.cy", "HUSS"),
    (114, "Marina", "Kyriacou", "mk114@aubmed.example.cy", "INDE"),
]
emit("-- Professors (fictional faculty; e-mail is optional)")
ins("Professor", ["professorId", "firstName", "lastName", "email", "departmentId"], professors)

requirements = [
    ("RQ001", "Grade 11 and 12 school transcripts", "Academic Record", "Official school records for grades 11 and 12"),
    ("RQ002", "Standardized exam score (SAT or ACT)", "Standardized Exam", "Best score is considered if several exams are sent"),
    ("RQ003", "Passport copy", "Identification", "Copy of the passport page with the photo"),
    ("RQ004", "English proficiency test (TOEFL or IELTS)", "Language Test", "Required after acceptance unless exempt"),
    ("RQ005", "Personal statement", "Statement", None),
    ("RQ006", "University transcripts (all institutions)", "Academic Record", "Official transcripts from every institution attended"),
    ("RQ007", "Recommendation letter 1", "Recommendation", "Academic or professional referee"),
    ("RQ008", "Recommendation letter 2", "Recommendation", "Academic or professional referee"),
    ("RQ009", "Statement of purpose", "Statement", "Graduate applicants only"),
    ("RQ010", "Curriculum vitae", "Other", None),
    ("RQ011", "GRE or GMAT score", "Standardized Exam", "Optional for graduate programs"),
    ("RQ012", "Additional supporting document", "Other", "Any extra document the applicant chooses to upload"),
]
emit("-- Admission requirements")
ins("Requirement", ["requirementId", "requirementName", "requirementType", "description"], requirements)

UG_REQ = [("RQ001", "Y"), ("RQ002", "Y"), ("RQ003", "Y"), ("RQ004", "Y"), ("RQ005", "N")]
GR_REQ = [("RQ003", "Y"), ("RQ004", "Y"), ("RQ006", "Y"), ("RQ007", "Y"), ("RQ008", "Y"),
          ("RQ009", "Y"), ("RQ010", "N"), ("RQ011", "N")]
pr_rows = []
for p in programs:
    for rid, m in (UG_REQ if p[2] == "Undergraduate" else GR_REQ):
        pr_rows.append((p[0], rid, m))
emit("-- Program requirements (M:N); isMandatory = 'N' marks optional items")
ins("ProgramRequirement", ["programId", "requirementId", "isMandatory"], pr_rows)

# ------------------------------------------------------------------ applicants
first_names = ["Lea", "Ahmad", "Sara", "Georgios", "Nour", "Elias", "Maria", "Yousef", "Christina",
               "Hassan", "Tala", "Nikos", "Rania", "Daniel", "Layal", "Ali", "Eleni", "Marc",
               "Dana", "Petros", "Zeina", "Samir", "Anna", "Karim", "Joelle", "Fares", "Ioanna",
               "Rami", "Hiba", "Michel", "Sophia", "Tarek", "Aya", "Stelios", "Mira", "Adam"]
last_names = ["Abboud", "Charalambous", "Haddad", "Papadopoulos", "Khalil", "Nicolaou", "Saad",
              "Antoniou", "Darwish", "Hajj", "Constantinou", "Moussa", "Kassab", "Vasiliou",
              "Ghanem", "Ibrahim", "Petrou", "Sleiman", "Hadjiyiannis", "Azar", "Frangieh",
              "Michael", "Tannous", "Zachariou", "Barakat", "Yammine", "Savva", "Farah",
              "Christodoulou", "Halabi", "Georgiades", "Mrad", "Stylianou", "Bitar", "Kyprianou", "Shami"]
middle = ["Maria", "Jean", "Antoine", "Rose", None, None, None, None, None, None]
nat_pool = ["Lebanese", "Cypriot", "Greek", "Jordanian", "Syrian", "Egyptian", "French",
            "Canadian", "American", "Iraqi", "Palestinian", "Italian", "British"]
country_code = {"Lebanese": "+961", "Cypriot": "+357", "Greek": "+30", "Jordanian": "+962",
                "Syrian": "+963", "Egyptian": "+20", "French": "+33", "Canadian": "+1",
                "American": "+1", "Iraqi": "+964", "Palestinian": "+970", "Italian": "+39", "British": "+44"}

N_APPLICANTS = 36
applicants, phones, nats = [], [], []
app_level = {}
for i in range(N_APPLICANTS):
    aid = 1001 + i
    fn, ln = first_names[i], last_names[i]
    grad = i % 5 == 4            # every fifth applicant is a graduate applicant
    app_level[aid] = "Graduate" if grad else "Undergraduate"
    by = random.randint(1996, 2001) if grad else random.randint(2006, 2009)
    dob = date(by, random.randint(1, 12), random.randint(1, 28))
    passport = random.choice("ABCDEFGHJKLMNPRSTUVWXYZ") + random.choice("ABCDEFGHJKLMNPRSTUVWXYZ") + str(random.randint(1000000, 9999999))
    email = f"{fn.lower()}.{ln.lower()}{random.randint(1, 99)}@mail.example.com"
    applicants.append((aid, passport, fn, middle[i % len(middle)], ln, dob.isoformat(), email))
    n1 = random.choice(nat_pool)
    nl = [n1]
    if random.random() < 0.35:                       # dual nationality
        n2 = random.choice([n for n in nat_pool if n != n1]); nl.append(n2)
    for n in nl: nats.append((aid, n))
    cc = country_code[nl[0]]
    phones.append((aid, f"{cc} {random.randint(70, 99)} {random.randint(100000, 999999)}", "Mobile"))
    if random.random() < 0.4:
        cc2 = country_code[nl[-1]]
        phones.append((aid, f"{cc2} {random.randint(20, 29)} {random.randint(100000, 999999)}",
                       random.choice(["Home", "Work"])))

emit("-- Applicants (fictional people; passport numbers and e-mails are invented)")
ins("Applicant", ["applicantId", "passportNo", "firstName", "middleName", "lastName", "dateOfBirth", "email"], applicants)
emit("-- Multivalued attribute: phone numbers")
ins("ApplicantPhone", ["applicantId", "phoneNumber", "phoneType"], phones)
emit("-- Multivalued attribute: nationalities")
ins("ApplicantNationality", ["applicantId", "nationality"], nats)

cycles = [(2024, "2023-11-15", "2024-03-01"), (2025, "2024-11-15", "2025-03-01"),
          (2026, "2025-11-15", "2026-03-01"), (2027, "2026-11-15", "2027-03-01")]
emit("-- Admission cycles (one intake per year, Fall term only)")
ins("AdmissionCycle", ["admissionYear", "earlyDeadline", "regularDeadline"], cycles)
cyc = {c[0]: (date.fromisoformat(c[1]), date.fromisoformat(c[2])) for c in cycles}

# ------------------------------------------------------------------ applications
ug_prog = [p[0] for p in programs if p[2] == "Undergraduate" and p[3] == "Active"]
gr_prog = [p[0] for p in programs if p[2] == "Graduate"]
prog_dept = {p[0]: p[5] for p in programs}
prog_level = {p[0]: p[2] for p in programs}
dept_profs = {}
for pr in professors: dept_profs.setdefault(pr[4], []).append(pr[0])

TODAY = date(2026, 11, 23)
applications = []
app_id = 50001
for aid in range(1001, 1001 + N_APPLICANTS):
    level = app_level[aid]
    year = random.choices([2024, 2025, 2026, 2027], weights=[2, 3, 4, 3])[0]
    n_apps = random.choices([1, 2, 3], weights=[5, 3, 1])[0]
    pool = ug_prog if level == "Undergraduate" else gr_prog
    chosen = random.sample(pool, min(n_apps, len(pool)))
    early_dl, reg_dl = cyc[year]
    for k, prog in enumerate(chosen):
        is_early = random.random() < 0.35
        if year == 2027:
            # current cycle: early round just closed, regular round open until TODAY
            if is_early:
                sub = early_dl - timedelta(days=random.randint(1, 40))
            else:
                sub = TODAY - timedelta(days=random.randint(0, 6))
        elif is_early:
            sub = early_dl - timedelta(days=random.randint(1, 50))
        else:
            sub = reg_dl - timedelta(days=random.randint(1, 95))
            if sub <= early_dl:
                sub = early_dl + timedelta(days=random.randint(5, 30))
        rnd = "Early" if is_early else "Regular"
        applications.append([app_id, aid, prog, year, "Fall", sub.isoformat(), rnd, "Submitted"])
        app_id += 1

emit("-- Applications (status starts as 'Submitted'; triggers update it when")
emit("-- reviews and decisions are inserted below)")
ins("Application", ["applicationId", "applicantId", "programId", "admissionYear", "admissionTerm",
                    "submissionDate", "admissionRound", "applicationStatus"], applications)

# ------------------------------------------------------------------ documents
docs = []
incomplete = set()
for a in applications:
    apid, aid, prog, year, _, sub, rnd, _ = a
    subd = date.fromisoformat(sub)
    reqs = UG_REQ if prog_level[prog] == "Undergraduate" else GR_REQ
    old = year < 2027
    n = 1
    for rid, mand in reqs:
        if rid == "RQ004" and not old and random.random() < 0.5:
            continue                                     # English test sent after acceptance
        if mand == "N" and random.random() < 0.5:
            continue
        if not old and random.random() < 0.12:
            if mand == "Y":
                incomplete.add(apid)                     # BR14: cannot be reviewed yet
            continue                                     # missing document (current cycle)
        up = subd - timedelta(days=random.randint(0, 10))
        if old:
            status = random.choices(["Verified", "Mismatch"], weights=[12, 1])[0]
        else:
            status = random.choices(["Pending", "Verified", "Mismatch"], weights=[5, 4, 1])[0]
        ext = "pdf" if random.random() < 0.85 else "jpg"
        docs.append((apid, n, rid, f"{apid}_{rid.lower()}.{ext}", up.isoformat(), status))
        n += 1
    if random.random() < 0.15:
        docs.append((apid, n, "RQ012", f"{apid}_extra.pdf", subd.isoformat(), "Pending" if not old else "Verified"))

emit("-- Weak entity: documents uploaded with each application")
ins("ApplicationDocument", ["applicationId", "documentNo", "requirementId", "fileName", "uploadDate",
                            "verificationStatus"], docs)

# ------------------------------------------------------------------ reviews
comments_hi = ["Strong academic record and clear goals.", "Excellent exam scores; recommend admission.",
               "Very well written statement.", "Consistent top grades in math and sciences.", None]
comments_mid = ["Solid file, average exam score.", "Good grades but a short statement.",
                "Recommendation letters are positive.", None, None]
comments_lo = ["Grades below the program average.", "Exam score under the expected range.",
               "Incomplete motivation in the statement.", None]
reviews, decisions, awards = [], [], []
dec_id, award_id = 9001, 7001
quality = {}
for a in applications:
    apid, aid, prog, year, _, sub, rnd, _ = a
    subd = date.fromisoformat(sub)
    q_ = quality.setdefault(aid, random.gauss(78, 10))
    profs = dept_profs[prog_dept[prog]]
    if year < 2027:
        n_rev = random.choice([2, 2, 3])
    else:
        n_rev = random.choices([0, 1, 2], weights=[5, 3, 2])[0] if rnd == "Regular" else random.choice([1, 2, 2, 3])
    if apid in incomplete:
        n_rev = 0
    revs = random.sample(profs, min(n_rev, len(profs)))
    scores = []
    last_review = subd
    for pid in revs:
        s = int(max(35, min(99, random.gauss(q_, 6))))
        rd = subd + timedelta(days=random.randint(7, 40))
        if rd > TODAY: rd = TODAY
        last_review = max(last_review, rd)
        c = random.choice(comments_hi if s >= 80 else comments_mid if s >= 65 else comments_lo)
        reviews.append((pid, apid, s, rd.isoformat(), c))
        scores.append(s)
    if year < 2027 and len(scores) >= 2:
        avg = sum(scores) / len(scores)
        dtype = "Accepted" if avg >= 74 else "Waitlisted" if avg >= 66 else "Rejected"
        dd = max(last_review + timedelta(days=random.randint(3, 20)),
                 date(year - 1, 12, 15) if rnd == "Early" else date(year, 4, 1))
        decisions.append((dec_id, apid, dtype, dd.isoformat())); dec_id += 1
        if dtype == "Accepted":
            ug = prog_level[prog] == "Undergraduate"
            if ug and rnd == "Early":                                     # BR21
                need = random.choice([0, 0, 20, 30, 40])
                pct = min(80, 20 + need)
                awards.append((award_id, apid, pct, "Merit" if need == 0 else "Need + Merit")); award_id += 1
            elif random.random() < 0.55:
                pct = random.choice([20, 30, 40, 50, 60, 70, 80] if ug else [10, 20, 30, 40])
                awards.append((award_id, apid, pct, "Need-Based")); award_id += 1
    elif year == 2027 and rnd == "Early" and len(scores) >= 2 and random.random() < 0.5:
        avg = sum(scores) / len(scores)
        dtype = "Accepted" if avg >= 74 else "Waitlisted" if avg >= 66 else "Rejected"
        decisions.append((dec_id, apid, dtype, "2026-11-20")); dec_id += 1
        if dtype == "Accepted" and prog_level[prog] == "Undergraduate":
            awards.append((award_id, apid, 20, "Merit")); award_id += 1

emit("-- Professor reviews (M:N relationship with attributes)")
ins("Review", ["professorId", "applicationId", "score", "reviewDate", "comments"], reviews)
emit("-- Admission decisions (1:1 with Application)")
ins("AdmissionDecision", ["decisionId", "applicationId", "decisionType", "decisionDate"], decisions)
emit("-- Financial aid awards (only for accepted applications, max 80 %)")
ins("FinancialAidAward", ["awardId", "applicationId", "aidPercentage", "awardType"], awards)

emit("COMMIT;")
open("/home/claude/project/sql/02_data.sql", "w").write("\n".join(out) + "\n")
print(len(applicants), "applicants", len(applications), "applications", len(docs), "docs",
      len(reviews), "reviews", len(decisions), "decisions", len(awards), "awards", len(phones), "phones", len(nats), "nats")
