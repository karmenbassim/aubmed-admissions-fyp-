-- =====================================================================
--  AUB Mediterraneo Admissions Database
--  File 3 of 3: queries used by the admissions office
--  Each query starts with "-- Q<n>:" followed by its purpose.
-- =====================================================================
PRAGMA foreign_keys = ON;

-- Q1: Open files of the current cycle (filtering + sorting).
--     Which 2027 applications are still waiting for a decision,
--     oldest submission first?
SELECT a.applicationId, ap.firstName || ' ' || ap.lastName AS applicant,
       a.programId, a.admissionRound, a.applicationStatus, a.submissionDate
FROM Application a
JOIN Applicant ap ON ap.applicantId = a.applicantId
WHERE a.admissionYear = 2027
  AND a.applicationStatus IN ('Submitted', 'Under Review')
ORDER BY a.submissionDate ASC, a.applicationId;

-- Q2: Accepted students of the 2026 intake with their program and
--     department (join across four tables).
SELECT d.decisionDate, ap.firstName || ' ' || ap.lastName AS student,
       p.programName, dep.departmentName, a.admissionRound
FROM AdmissionDecision d
JOIN Application a  ON a.applicationId = d.applicationId
JOIN Applicant  ap  ON ap.applicantId  = a.applicantId
JOIN Program    p   ON p.programId     = a.programId
JOIN Department dep ON dep.departmentId = p.departmentId
WHERE d.decisionType = 'Accepted' AND a.admissionYear = 2026
ORDER BY p.programName, student;

-- Q3: Applications that are missing a mandatory document required by
--     their program (NOT EXISTS sub-query). Supports rule BR14.
SELECT a.applicationId, ap.lastName, a.programId, r.requirementName
FROM Application a
JOIN Applicant ap          ON ap.applicantId = a.applicantId
JOIN ProgramRequirement pr ON pr.programId   = a.programId AND pr.isMandatory = 'Y'
JOIN Requirement r         ON r.requirementId = pr.requirementId
WHERE a.applicationStatus <> 'Decided'
  AND r.requirementId <> 'RQ004'          -- English test is due after acceptance (BR19)
  AND NOT EXISTS (SELECT 1 FROM ApplicationDocument doc
                   WHERE doc.applicationId = a.applicationId
                     AND doc.requirementId = pr.requirementId)
ORDER BY a.applicationId, r.requirementId;

-- Q4: Number of applications per program and admission year
--     (aggregate + GROUP BY).
SELECT p.programId, p.programName, a.admissionYear, COUNT(*) AS applications
FROM Application a
JOIN Program p ON p.programId = a.programId
GROUP BY p.programId, p.programName, a.admissionYear
ORDER BY a.admissionYear, applications DESC;

-- Q5: Acceptance rate per program, only for programs with at least
--     five decisions (GROUP BY + HAVING).
SELECT p.programId,
       COUNT(*)                                                  AS decisions,
       SUM(CASE WHEN d.decisionType = 'Accepted' THEN 1 ELSE 0 END) AS accepted,
       ROUND(100.0 * SUM(CASE WHEN d.decisionType = 'Accepted' THEN 1 ELSE 0 END)
             / COUNT(*), 1)                                      AS acceptanceRatePct
FROM AdmissionDecision d
JOIN Application a ON a.applicationId = d.applicationId
JOIN Program p     ON p.programId     = a.programId
GROUP BY p.programId
HAVING COUNT(*) >= 5
ORDER BY acceptanceRatePct DESC;

-- Q6: Shortlist for the current cycle: applications whose derived average
--     review score is 75 or more after at least two reviews
--     (derived attribute + HAVING).
SELECT a.applicationId, ap.firstName || ' ' || ap.lastName AS applicant,
       a.programId, COUNT(r.professorId) AS reviews,
       ROUND(AVG(r.score), 1) AS averageScore
FROM Application a
JOIN Applicant ap ON ap.applicantId = a.applicantId
JOIN Review r     ON r.applicationId = a.applicationId
WHERE a.admissionYear = 2027
GROUP BY a.applicationId
HAVING COUNT(r.professorId) >= 2 AND AVG(r.score) >= 75
ORDER BY averageScore DESC;

-- Q7: Reviewer workload: reviews completed per professor and the number
--     of open (undecided) files they are reviewing (LEFT JOIN + GROUP BY).
SELECT pr.professorId, pr.firstName || ' ' || pr.lastName AS professor,
       pr.departmentId,
       COUNT(r.applicationId) AS totalReviews,
       SUM(CASE WHEN a.applicationStatus <> 'Decided' THEN 1 ELSE 0 END) AS openFiles,
       ROUND(AVG(r.score), 1) AS avgScoreGiven
FROM Professor pr
LEFT JOIN Review r      ON r.professorId  = pr.professorId
LEFT JOIN Application a ON a.applicationId = r.applicationId
GROUP BY pr.professorId
ORDER BY totalReviews DESC, openFiles DESC;

-- Q8: Average financial aid offered per program (percentage and the
--     derived amount in EUR = percentage x annual tuition).
SELECT p.programId, p.degreeLevel, COUNT(f.awardId) AS awards,
       ROUND(AVG(f.aidPercentage), 1) AS avgAidPct,
       ROUND(AVG(f.aidPercentage / 100.0 * p.annualTuition), 0) AS avgAidEUR,
       MAX(f.aidPercentage) AS maxAidPct
FROM FinancialAidAward f
JOIN Application a ON a.applicationId = f.applicationId
JOIN Program p     ON p.programId     = a.programId
GROUP BY p.programId, p.degreeLevel
ORDER BY avgAidPct DESC;

-- Q9: Document verification queue: open applications with at least one
--     document that is still pending or did not match the typed data
--     (GROUP BY + HAVING). This targets the manual checks described by
--     the admissions office during the site visit.
SELECT a.applicationId, ap.lastName, a.programId,
       SUM(doc.verificationStatus = 'Pending')  AS pendingDocs,
       SUM(doc.verificationStatus = 'Mismatch') AS mismatchDocs,
       COUNT(*)                                 AS totalDocs
FROM ApplicationDocument doc
JOIN Application a ON a.applicationId = doc.applicationId
JOIN Applicant ap  ON ap.applicantId  = a.applicantId
WHERE a.applicationStatus <> 'Decided'
GROUP BY a.applicationId
HAVING SUM(doc.verificationStatus IN ('Pending', 'Mismatch')) > 0
ORDER BY mismatchDocs DESC, pendingDocs DESC;

-- Q10: Applicants holding more than one nationality (multivalued
--      attribute, GROUP BY + HAVING).
SELECT ap.applicantId, ap.firstName || ' ' || ap.lastName AS applicant,
       COUNT(*) AS nationalities, group_concat(n.nationality, ' / ') AS list
FROM Applicant ap
JOIN ApplicantNationality n ON n.applicantId = ap.applicantId
GROUP BY ap.applicantId
HAVING COUNT(*) > 1
ORDER BY ap.lastName;

-- Q11: Early versus regular round: decisions and acceptance rate
--      (aggregate on a CASE expression).
SELECT a.admissionRound,
       COUNT(*) AS decided,
       SUM(d.decisionType = 'Accepted')   AS accepted,
       SUM(d.decisionType = 'Waitlisted') AS waitlisted,
       SUM(d.decisionType = 'Rejected')   AS rejected,
       ROUND(100.0 * SUM(d.decisionType = 'Accepted') / COUNT(*), 1) AS acceptanceRatePct
FROM Application a
JOIN AdmissionDecision d ON d.applicationId = a.applicationId
GROUP BY a.admissionRound;

-- Q12: Average applicant age (derived from date of birth) by degree level
--      of the program applied to, using the vw_ApplicantProfile view.
SELECT p.degreeLevel,
       COUNT(DISTINCT v.applicantId) AS applicants,
       ROUND(AVG(v.age), 1) AS avgAge, MIN(v.age) AS youngest, MAX(v.age) AS oldest
FROM vw_ApplicantProfile v
JOIN Application a ON a.applicantId = v.applicantId
JOIN Program p     ON p.programId   = a.programId
GROUP BY p.degreeLevel;

-- Q13: Search by name or passport (the same query is used by the
--      website search box; here the search text is 'had').
SELECT applicantId, firstName, lastName, passportNo, email
FROM Applicant
WHERE lastName LIKE '%had%' OR firstName LIKE '%had%' OR passportNo LIKE '%had%'
ORDER BY lastName;
