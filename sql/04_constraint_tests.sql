-- =====================================================================
--  AUB Mediterraneo Admissions Database
--  Optional file: integrity tests. Every statement below is EXPECTED to
--  FAIL and shows which constraint or trigger stops it. Run each
--  statement on its own (for example in DB Browser for SQLite) or with
--  tools/run_tests.py, which reports the error message of each one.
-- =====================================================================
PRAGMA foreign_keys = ON;

-- T1  CHAR(5) length check on Program.programId
INSERT INTO Program VALUES ('UGX', 'BS in Test', 'Undergraduate', 'Active', 10000, 'CMPS');

-- T2  Allowed choices: degreeLevel must be Undergraduate or Graduate
INSERT INTO Program VALUES ('UGTST', 'BS in Test', 'Diploma', 'Active', 10000, 'CMPS');

-- T3  Range: a review score must be between 0 and 100
--     (professor 111 belongs to HUSS, which offers program UGPPE of file 50008)
INSERT INTO Review VALUES (111, 50008, 120, '2026-11-22', NULL);

-- T4  Secondary key: two applicants cannot share a passport number (BR24)
INSERT INTO Applicant (applicantId, passportNo, firstName, lastName, dateOfBirth, email)
SELECT 9999, passportNo, 'Copy', 'Person', '2007-01-01', 'copy@mail.example.com'
FROM Applicant WHERE applicantId = 1001;

-- T5  Referential integrity: the program must exist
INSERT INTO Application (applicationId, applicantId, programId, admissionYear, submissionDate)
VALUES (59990, 1001, 'ZZZZZ', 2027, '2026-11-20');

-- T6  BR3: only one application per program per cycle
INSERT INTO Application (applicationId, applicantId, programId, admissionYear, submissionDate)
SELECT 59991, applicantId, programId, admissionYear, submissionDate
FROM Application WHERE applicationId = 50008;

-- T7  BR6: an Early application after the early deadline is refused
INSERT INTO Application (applicationId, applicantId, programId, admissionYear,
                         submissionDate, admissionRound)
VALUES (59992, 1036, 'UGPSY', 2027, '2026-11-20', 'Early');

-- T8  BR20: financial aid for an application that was not accepted
INSERT INTO FinancialAidAward (awardId, applicationId, aidPercentage)
SELECT 7999, applicationId, 30 FROM AdmissionDecision
WHERE decisionType = 'Rejected' LIMIT 1;

-- T9  BR22: aid above the 80 % cap
INSERT INTO FinancialAidAward (awardId, applicationId, aidPercentage)
SELECT 7998, d.applicationId, 90 FROM AdmissionDecision d
WHERE d.decisionType = 'Accepted'
  AND d.applicationId NOT IN (SELECT applicationId FROM FinancialAidAward) LIMIT 1;

-- T10 BR15: a professor from another department cannot review the file
--     (professor 101 belongs to CMPS, while file 50008 is for UGPPE, offered by HUSS)
INSERT INTO Review (professorId, applicationId, score, reviewDate)
VALUES (101, 50008, 70, '2026-11-22');

-- T11 BR18: a decision cannot be issued before two reviews exist
INSERT INTO AdmissionDecision (decisionId, applicationId, decisionType, decisionDate)
SELECT 9999, a.applicationId, 'Accepted', '2026-11-23' FROM Application a
WHERE (SELECT COUNT(*) FROM Review r WHERE r.applicationId = a.applicationId) = 0 LIMIT 1;

-- T12 1:1 relationship: an application cannot receive a second decision
INSERT INTO AdmissionDecision (decisionId, applicationId, decisionType, decisionDate)
SELECT 9998, applicationId, 'Rejected', '2026-11-23' FROM AdmissionDecision LIMIT 1;
