-- =====================================================================
--  AUB Mediterraneo Admissions Database
--  INDE 513 Information Systems - Project Phase II
--  File 1 of 3: table definitions, triggers and views (SQLite 3)
--
--  Run order:  01_schema.sql  ->  02_data.sql  ->  03_queries.sql
--  Example:    sqlite3 admissions.db < 01_schema.sql
-- =====================================================================

PRAGMA foreign_keys = ON;

-- Drop in reverse dependency order so the script can be re-run
DROP VIEW  IF EXISTS vw_ApplicationSummary;
DROP VIEW  IF EXISTS vw_ApplicantProfile;
DROP TABLE IF EXISTS FinancialAidAward;
DROP TABLE IF EXISTS AdmissionDecision;
DROP TABLE IF EXISTS Review;
DROP TABLE IF EXISTS ApplicationDocument;
DROP TABLE IF EXISTS Application;
DROP TABLE IF EXISTS AdmissionCycle;
DROP TABLE IF EXISTS ApplicantNationality;
DROP TABLE IF EXISTS ApplicantPhone;
DROP TABLE IF EXISTS Applicant;
DROP TABLE IF EXISTS ProgramRequirement;
DROP TABLE IF EXISTS Requirement;
DROP TABLE IF EXISTS Professor;
DROP TABLE IF EXISTS Program;
DROP TABLE IF EXISTS Department;

-- ---------------------------------------------------------------------
-- 1. Department  (strong entity)
-- ---------------------------------------------------------------------
CREATE TABLE Department (
    departmentId    CHAR(4)      PRIMARY KEY
                    CHECK (length(departmentId) = 4 AND departmentId = upper(departmentId)),
    departmentName  VARCHAR(60)  NOT NULL UNIQUE
                    CHECK (length(departmentName) BETWEEN 3 AND 60)
);

-- ---------------------------------------------------------------------
-- 2. Program  (strong entity; Department Offers Program 1:N)
-- ---------------------------------------------------------------------
CREATE TABLE Program (
    programId       CHAR(5)      PRIMARY KEY
                    CHECK (length(programId) = 5 AND programId = upper(programId)),
    programName     VARCHAR(80)  NOT NULL UNIQUE
                    CHECK (length(programName) BETWEEN 3 AND 80),
    degreeLevel     VARCHAR(13)  NOT NULL
                    CHECK (degreeLevel IN ('Undergraduate', 'Graduate')),
    programStatus   VARCHAR(9)   NOT NULL DEFAULT 'Active'
                    CHECK (programStatus IN ('Active', 'Planned', 'Suspended')),
    annualTuition   NUMERIC(8,2) NOT NULL
                    CHECK (annualTuition BETWEEN 0 AND 100000),
    departmentId    CHAR(4)      NOT NULL,
    FOREIGN KEY (departmentId) REFERENCES Department(departmentId)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- 3. Professor  (strong entity; Professor BelongsTo Department N:1)
-- ---------------------------------------------------------------------
CREATE TABLE Professor (
    professorId     INTEGER      PRIMARY KEY
                    CHECK (professorId BETWEEN 100 AND 999),
    firstName       VARCHAR(30)  NOT NULL,
    lastName        VARCHAR(30)  NOT NULL,
    email           VARCHAR(80)  UNIQUE
                    CHECK (email IS NULL OR email LIKE '%_@_%._%'),
    departmentId    CHAR(4)      NOT NULL,
    FOREIGN KEY (departmentId) REFERENCES Department(departmentId)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- 4. Requirement  (strong entity)
-- ---------------------------------------------------------------------
CREATE TABLE Requirement (
    requirementId   CHAR(5)      PRIMARY KEY
                    CHECK (length(requirementId) = 5 AND requirementId LIKE 'RQ%'),
    requirementName VARCHAR(60)  NOT NULL UNIQUE,
    requirementType VARCHAR(17)  NOT NULL
                    CHECK (requirementType IN ('Academic Record', 'Standardized Exam',
                                               'Recommendation', 'Statement',
                                               'Language Test', 'Identification', 'Other')),
    description     VARCHAR(200)
);

-- ---------------------------------------------------------------------
-- 5. ProgramRequirement  (M:N  Program Requires Requirement)
-- ---------------------------------------------------------------------
CREATE TABLE ProgramRequirement (
    programId       CHAR(5)      NOT NULL,
    requirementId   CHAR(5)      NOT NULL,
    isMandatory     CHAR(1)      NOT NULL DEFAULT 'Y'
                    CHECK (isMandatory IN ('Y', 'N')),
    PRIMARY KEY (programId, requirementId),
    FOREIGN KEY (programId)     REFERENCES Program(programId)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (requirementId) REFERENCES Requirement(requirementId)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- 6. Applicant  (strong entity; primary key + secondary key passportNo)
-- ---------------------------------------------------------------------
CREATE TABLE Applicant (
    applicantId     INTEGER      PRIMARY KEY
                    CHECK (applicantId BETWEEN 1000 AND 99999),
    passportNo      VARCHAR(15)  NOT NULL UNIQUE
                    CHECK (length(passportNo) BETWEEN 6 AND 15),
    firstName       VARCHAR(30)  NOT NULL,
    middleName      VARCHAR(30),
    lastName        VARCHAR(30)  NOT NULL,
    dateOfBirth     DATE         NOT NULL
                    CHECK (dateOfBirth = date(dateOfBirth) AND dateOfBirth > '1950-01-01'),
    email           VARCHAR(80)  NOT NULL UNIQUE
                    CHECK (email LIKE '%_@_%._%')
);

-- 7. ApplicantPhone  (multivalued attribute PhoneNumber)
CREATE TABLE ApplicantPhone (
    applicantId     INTEGER      NOT NULL,
    phoneNumber     VARCHAR(20)  NOT NULL
                    CHECK (phoneNumber LIKE '+%' AND length(phoneNumber) BETWEEN 8 AND 20),
    phoneType       VARCHAR(6)   NOT NULL DEFAULT 'Mobile'
                    CHECK (phoneType IN ('Mobile', 'Home', 'Work')),
    PRIMARY KEY (applicantId, phoneNumber),
    FOREIGN KEY (applicantId) REFERENCES Applicant(applicantId)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 8. ApplicantNationality  (multivalued attribute Nationality)
CREATE TABLE ApplicantNationality (
    applicantId     INTEGER      NOT NULL,
    nationality     VARCHAR(40)  NOT NULL,
    PRIMARY KEY (applicantId, nationality),
    FOREIGN KEY (applicantId) REFERENCES Applicant(applicantId)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- 9. AdmissionCycle  (added in Phase II during normalization:
--    the deadlines depend on the admission year, not on the application)
-- ---------------------------------------------------------------------
CREATE TABLE AdmissionCycle (
    admissionYear   INTEGER      PRIMARY KEY
                    CHECK (admissionYear BETWEEN 2023 AND 2100),
    earlyDeadline   DATE         NOT NULL CHECK (earlyDeadline   = date(earlyDeadline)),
    regularDeadline DATE         NOT NULL CHECK (regularDeadline = date(regularDeadline)),
    CHECK (earlyDeadline < regularDeadline)
);

-- ---------------------------------------------------------------------
-- 10. Application  (Applicant Submits 1:N, Targets Program N:1,
--                   BelongsTo AdmissionCycle N:1)
-- ---------------------------------------------------------------------
CREATE TABLE Application (
    applicationId     INTEGER     PRIMARY KEY
                      CHECK (applicationId BETWEEN 50000 AND 99999),
    applicantId       INTEGER     NOT NULL,
    programId         CHAR(5)     NOT NULL,
    admissionYear     INTEGER     NOT NULL,
    admissionTerm     VARCHAR(4)  NOT NULL DEFAULT 'Fall'
                      CHECK (admissionTerm = 'Fall'),                    -- BR4
    submissionDate    DATE        NOT NULL
                      CHECK (submissionDate = date(submissionDate)),
    admissionRound    VARCHAR(7)  NOT NULL DEFAULT 'Regular'
                      CHECK (admissionRound IN ('Early', 'Regular')),
    applicationStatus VARCHAR(12) NOT NULL DEFAULT 'Submitted'
                      CHECK (applicationStatus IN ('Submitted', 'Under Review', 'Decided')),
    UNIQUE (applicantId, programId, admissionYear),                      -- BR3
    FOREIGN KEY (applicantId)   REFERENCES Applicant(applicantId)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (programId)     REFERENCES Program(programId)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (admissionYear) REFERENCES AdmissionCycle(admissionYear)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- 11. ApplicationDocument  (weak entity, owner Application,
--     discriminator documentNo; Fulfills Requirement N:1)
-- ---------------------------------------------------------------------
CREATE TABLE ApplicationDocument (
    applicationId      INTEGER     NOT NULL,
    documentNo         INTEGER     NOT NULL CHECK (documentNo BETWEEN 1 AND 30),
    requirementId      CHAR(5)     NOT NULL,
    fileName           VARCHAR(60) NOT NULL,
    uploadDate         DATE        NOT NULL CHECK (uploadDate = date(uploadDate)),
    verificationStatus VARCHAR(8)  NOT NULL DEFAULT 'Pending'
                       CHECK (verificationStatus IN ('Pending', 'Verified', 'Mismatch')),
    PRIMARY KEY (applicationId, documentNo),
    FOREIGN KEY (applicationId) REFERENCES Application(applicationId)
        ON UPDATE CASCADE ON DELETE CASCADE,                             -- BR12
    FOREIGN KEY (requirementId) REFERENCES Requirement(requirementId)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- 12. Review  (M:N  Professor Reviews Application, with attributes)
-- ---------------------------------------------------------------------
CREATE TABLE Review (
    professorId     INTEGER      NOT NULL,
    applicationId   INTEGER      NOT NULL,
    score           INTEGER      NOT NULL CHECK (score BETWEEN 0 AND 100), -- BR16
    reviewDate      DATE         NOT NULL CHECK (reviewDate = date(reviewDate)),
    comments        VARCHAR(300),
    PRIMARY KEY (professorId, applicationId),                              -- one review each
    FOREIGN KEY (professorId)   REFERENCES Professor(professorId)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (applicationId) REFERENCES Application(applicationId)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- 13. AdmissionDecision  (1:1  Application ResultsIn AdmissionDecision)
-- ---------------------------------------------------------------------
CREATE TABLE AdmissionDecision (
    decisionId      INTEGER      PRIMARY KEY CHECK (decisionId BETWEEN 9000 AND 9999),
    applicationId   INTEGER      NOT NULL UNIQUE,                        -- 1:1, mandatory
    decisionType    VARCHAR(10)  NOT NULL
                    CHECK (decisionType IN ('Accepted', 'Rejected', 'Waitlisted')),
    decisionDate    DATE         NOT NULL CHECK (decisionDate = date(decisionDate)),
    FOREIGN KEY (applicationId) REFERENCES Application(applicationId)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- 14. FinancialAidAward  (1:1  Application Receives FinancialAidAward)
-- ---------------------------------------------------------------------
CREATE TABLE FinancialAidAward (
    awardId         INTEGER      PRIMARY KEY CHECK (awardId BETWEEN 7000 AND 7999),
    applicationId   INTEGER      NOT NULL UNIQUE,                        -- 1:1, mandatory
    aidPercentage   NUMERIC(5,2) NOT NULL
                    CHECK (aidPercentage > 0 AND aidPercentage <= 80),   -- BR22
    awardType       VARCHAR(12)  NOT NULL DEFAULT 'Need-Based'
                    CHECK (awardType IN ('Need-Based', 'Merit', 'Need + Merit')),
    FOREIGN KEY (applicationId) REFERENCES Application(applicationId)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- Indexes on foreign keys that are searched often (see data dictionary)
CREATE INDEX idx_program_department    ON Program(departmentId);
CREATE INDEX idx_professor_department  ON Professor(departmentId);
CREATE INDEX idx_application_applicant ON Application(applicantId);
CREATE INDEX idx_application_program   ON Application(programId);
CREATE INDEX idx_applicant_lastname    ON Applicant(lastName);

-- =====================================================================
--  TRIGGERS: business rules that a CHECK constraint cannot express
-- =====================================================================

-- BR3: at most 3 applications per applicant in one admission cycle
CREATE TRIGGER trg_application_max_three
BEFORE INSERT ON Application
WHEN (SELECT COUNT(*) FROM Application
       WHERE applicantId = NEW.applicantId
         AND admissionYear = NEW.admissionYear) >= 3
BEGIN
    SELECT RAISE(ABORT, 'BR3: an applicant may submit at most 3 applications per admission cycle');
END;

-- BR6: an application counts as Early only if submitted by the early deadline,
--      and no application is accepted after the regular deadline
CREATE TRIGGER trg_application_deadlines
BEFORE INSERT ON Application
BEGIN
    SELECT CASE
        WHEN NEW.admissionRound = 'Early' AND NEW.submissionDate >
             (SELECT earlyDeadline FROM AdmissionCycle WHERE admissionYear = NEW.admissionYear)
        THEN RAISE(ABORT, 'BR6: early applications must be submitted by the early deadline')
        WHEN NEW.submissionDate >
             (SELECT regularDeadline FROM AdmissionCycle WHERE admissionYear = NEW.admissionYear)
        THEN RAISE(ABORT, 'BR6: the regular deadline for this cycle has passed')
    END;
END;

-- BR15: a reviewer must belong to the department that offers the program
CREATE TRIGGER trg_review_same_department
BEFORE INSERT ON Review
WHEN (SELECT departmentId FROM Professor WHERE professorId = NEW.professorId) <>
     (SELECT p.departmentId FROM Application a JOIN Program p ON p.programId = a.programId
       WHERE a.applicationId = NEW.applicationId)
BEGIN
    SELECT RAISE(ABORT, 'BR15: the reviewer must belong to the department offering the program');
END;

-- BR14: a file can be reviewed only when every mandatory document is uploaded
--       (the English test is due after acceptance, BR19, so it is not checked)
CREATE TRIGGER trg_review_documents_complete
BEFORE INSERT ON Review
WHEN EXISTS (SELECT 1 FROM Application a
               JOIN ProgramRequirement pr ON pr.programId = a.programId
              WHERE a.applicationId = NEW.applicationId
                AND pr.isMandatory = 'Y' AND pr.requirementId <> 'RQ004'
                AND NOT EXISTS (SELECT 1 FROM ApplicationDocument d
                                 WHERE d.applicationId = a.applicationId
                                   AND d.requirementId = pr.requirementId))
BEGIN
    SELECT RAISE(ABORT, 'BR14: mandatory documents are missing, the file cannot be reviewed yet');
END;

-- Reviews: (2,3) participation - no more than 3 reviewers per application
CREATE TRIGGER trg_review_max_three
BEFORE INSERT ON Review
WHEN (SELECT COUNT(*) FROM Review WHERE applicationId = NEW.applicationId) >= 3
BEGIN
    SELECT RAISE(ABORT, 'An application cannot have more than 3 reviewers');
END;

-- A review cannot be dated before the application was submitted
CREATE TRIGGER trg_review_date
BEFORE INSERT ON Review
WHEN NEW.reviewDate < (SELECT submissionDate FROM Application WHERE applicationId = NEW.applicationId)
BEGIN
    SELECT RAISE(ABORT, 'A review cannot be dated before the submission date');
END;

-- First review moves the application from Submitted to Under Review
CREATE TRIGGER trg_review_status
AFTER INSERT ON Review
BEGIN
    UPDATE Application SET applicationStatus = 'Under Review'
     WHERE applicationId = NEW.applicationId AND applicationStatus = 'Submitted';
END;

-- BR15/BR18: a decision needs at least two completed reviews
CREATE TRIGGER trg_decision_needs_reviews
BEFORE INSERT ON AdmissionDecision
WHEN (SELECT COUNT(*) FROM Review WHERE applicationId = NEW.applicationId) < 2
BEGIN
    SELECT RAISE(ABORT, 'BR18: a decision requires at least two completed reviews');
END;

-- Recording a decision closes the application
CREATE TRIGGER trg_decision_status
AFTER INSERT ON AdmissionDecision
BEGIN
    UPDATE Application SET applicationStatus = 'Decided'
     WHERE applicationId = NEW.applicationId;
END;

-- BR20: financial aid only for accepted applications
CREATE TRIGGER trg_aid_only_accepted
BEFORE INSERT ON FinancialAidAward
WHEN NOT EXISTS (SELECT 1 FROM AdmissionDecision
                  WHERE applicationId = NEW.applicationId AND decisionType = 'Accepted')
BEGIN
    SELECT RAISE(ABORT, 'BR20: financial aid can only be offered to accepted applications');
END;

-- =====================================================================
--  VIEWS: derived attributes are calculated, never stored
-- =====================================================================

-- Applicant.age (derived from dateOfBirth)
CREATE VIEW vw_ApplicantProfile AS
SELECT a.applicantId,
       a.firstName || COALESCE(' ' || a.middleName, '') || ' ' || a.lastName AS fullName,
       a.passportNo,
       a.dateOfBirth,
       CAST((julianday('now') - julianday(a.dateOfBirth)) / 365.25 AS INTEGER) AS age,
       a.email,
       (SELECT group_concat(nationality, ', ') FROM ApplicantNationality n
         WHERE n.applicantId = a.applicantId) AS nationalities,
       (SELECT group_concat(phoneNumber, ', ') FROM ApplicantPhone p
         WHERE p.applicantId = a.applicantId) AS phones
FROM Applicant a;

-- Application.averageReviewScore and Application.daysSinceSubmission (derived),
-- plus the derived aid amount = aidPercentage x annual tuition
CREATE VIEW vw_ApplicationSummary AS
SELECT ap.applicationId,
       ap.applicantId,
       ac.firstName || ' ' || ac.lastName                          AS applicantName,
       ap.programId,
       p.programName,
       p.degreeLevel,
       ap.admissionYear,
       ap.admissionRound,
       ap.applicationStatus,
       ap.submissionDate,
       CAST(julianday('now') - julianday(ap.submissionDate) AS INTEGER) AS daysSinceSubmission,
       (SELECT COUNT(*) FROM Review r WHERE r.applicationId = ap.applicationId) AS reviewCount,
       (SELECT ROUND(AVG(score), 1) FROM Review r
         WHERE r.applicationId = ap.applicationId)                 AS averageReviewScore,
       d.decisionType,
       d.decisionDate,
       f.aidPercentage,
       ROUND(f.aidPercentage / 100.0 * p.annualTuition, 2)         AS aidAmount
FROM Application ap
JOIN Applicant  ac ON ac.applicantId = ap.applicantId
JOIN Program    p  ON p.programId    = ap.programId
LEFT JOIN AdmissionDecision d ON d.applicationId = ap.applicationId
LEFT JOIN FinancialAidAward f ON f.applicationId = ap.applicationId;
