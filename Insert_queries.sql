USE research_lab;
SET FOREIGN_KEY_CHECKS = 0;

-- Clear previous data (safe-reset)
DELETE FROM PUBLISHES; DELETE FROM PUBLICATION; DELETE FROM USES;
DELETE FROM EQUIPMENT; DELETE FROM WORKS; DELETE FROM FUNDS;
DELETE FROM PROJECT; DELETE FROM STUDENT; DELETE FROM FACULTY;
DELETE FROM COLLABORATOR; DELETE FROM LAB_MEMBER; DELETE FROM GRANT_INFO;

-- =====================================================
-- GRANTS (explicit IDs so links are stable)
-- =====================================================
INSERT INTO GRANT_INFO (GID, Source, Budget, StartDate, Duration) VALUES
(1001, 'NSF - National Science Foundation', 500000.00, '2023-01-01', 48),
(1002, 'DARPA - AI Strategic Initiative', 1200000.00, '2024-06-01', 24),
(1003, 'NJIT Internal Research Fund', 50000.00, '2025-01-15', 12),
(1004, 'Google DeepMind Research', 75000.00, '2023-09-01', 18),
(1005, 'Wellcome Trust - Health Data', 200000.00, '2024-03-01', 36);

-- =====================================================
-- LAB MEMBERS (20 total: mix of Faculty + Students + Staff)
-- NOTE: explicit MID values used to keep links stable
-- =====================================================
INSERT INTO LAB_MEMBER (MID, Name, JoinDate, MType, Mentor) VALUES
(1,  'Dr. Keith Williams',  '2015-08-20', 'Faculty', NULL),
(2,  'Dr. John McCarthy',   '2018-01-15', 'Faculty', NULL),
(3,  'Dr. Ada Lovelace',    '2020-09-01', 'Faculty', NULL),
(4,  'Dr. Grace Hopper',    '2017-04-12', 'Faculty', NULL),
(5,  'Dr. Tim Berners-Lee', '2016-11-05', 'Faculty', NULL),

(10, 'Mohammed Saim',       '2025-09-01', 'Student', 1),
(11, 'Alice Johnson',       '2024-01-10', 'Student', 1),
(12, 'Bob Smith',           '2023-09-01', 'Student', 2),
(13, 'Charlie Brown',       '2025-01-20', 'Student', 2),
(14, 'Diana Prince',        '2024-05-15', 'Student', 3),
(15, 'Evan Wright',         '2025-09-01', 'Student', 1),
(16, 'Fiona Green',         '2024-08-12', 'Student', 3),
(17, 'George Miller',       '2023-06-01', 'Student', 4),
(18, 'Hannah Lee',          '2022-09-20', 'Student', 4),
(19, 'Ibrahim Khan',        '2023-11-11', 'Student', 2),
(20, 'Julia Roberts',       '2022-12-05', 'Student', 3),
(21, 'Kevin Patel',         '2021-07-30', 'Staff',   NULL),
(22, 'Laura Chen',          '2020-03-25', 'Staff',   NULL),
(23, 'Mason Clark',         '2021-10-02', 'Staff',   NULL);

-- Faculty table (if used in schema)
INSERT INTO FACULTY (MID, Department) VALUES
(1, 'Computer Science'), (2, 'Artificial Intelligence'), (3, 'Data Science'),
(4, 'Robotics'), (5, 'Security');

-- STUDENT (matching the student MIDs above)
-- (Assumes STUDENT has columns: MID, SID, Level, Major)
INSERT INTO STUDENT (MID, SID, Level, Major) VALUES
(10, 10010, 'Masters', 'Computer Science'),
(11, 10011, 'PhD',     'Computer Science'),
(12, 10012, 'PhD',     'Artificial Intelligence'),
(13, 10013, 'Masters', 'Artificial Intelligence'),
(14, 10014, 'Masters', 'Data Science'),
(15, 10015, 'Masters', 'Computer Science'),
(16, 10016, 'PhD',     'Data Science'),
(17, 10017, 'Masters', 'Robotics'),
(18, 10018, 'PhD',     'Electrical Engineering'),
(19, 10019, 'Masters', 'Signal Processing'),
(20, 10020, 'PhD',     'Bioinformatics');

-- =====================================================
-- PROJECTS (10 projects: 501..510)
-- Columns assumed: PID, Title, SDate, EDate, EDuration, Leader
-- =====================================================
INSERT INTO PROJECT (PID, Title, SDate, EDate, EDuration, Leader) VALUES
(501, 'Autonomous Drone Navigation',         '2024-01-01', '2026-12-31', 36, 1),
(502, 'Natural Language Processing for Law', '2024-06-01', '2026-06-01', 24, 2),
(503, 'Big Data Health Analytics',           '2025-02-01', '2025-12-01', 10, 3),
(504, 'Quantum Cryptography',                '2023-09-01', '2024-09-01', 12, 1),
(505, 'Robotic Manipulation Suite',          '2024-03-01', NULL,        24, 4),
(506, 'Graph Neural Networks',               '2024-05-15', '2025-11-15', 18, 2),
(507, 'Bioinformatics Pipeline',             '2023-11-01', '2025-11-30', 24, 3),
(508, 'Edge AI Devices',                     '2025-01-01', NULL,        36, 1),
(509, 'Secure Distributed Systems',          '2024-02-01', '2025-08-31', 18, 5),
(510, 'Human-Robot Interaction',             '2024-07-01', NULL,        24, 4);

-- =====================================================
-- FUNDS: link grants to projects
-- (GID, PID)
-- =====================================================
INSERT INTO FUNDS (GID, PID) VALUES
(1001, 501),
(1002, 502),
(1003, 503),
(1004, 504),
(1005, 507);

-- =====================================================
-- WORKS: who works on which project (PID, MID, Role, Hours)
-- =====================================================
INSERT INTO WORKS (PID, MID, Role, Hours) VALUES
(501, 1,   'Principal Investigator', 12.0),
(501, 10,  'Research Assistant', 20.0),
(501, 11,  'Lead Developer', 15.0),
(501, 15,  'Intern', 10.0),

(502, 2,   'Principal Investigator', 10.0),
(502, 12,  'Data Analyst', 25.0),
(502, 13,  'Tester', 10.0),
(502, 21,  'Engineer', 12.0),

(503, 3,   'Principal Investigator', 12.0),
(503, 14,  'Statistician', 18.0),
(503, 16,  'Research Asst', 15.0),

(504, 1,   'Principal Investigator', 8.0),
(504, 17,  'DevOps', 10.0),

(505, 4,   'PI', 10.0),
(505, 18,  'RA', 20.0),

(506, 2,   'PI', 8.0),
(506, 19,  'Researcher', 14.0),

(507, 3,   'PI', 12.0),
(507, 20,  'Bioinfo', 18.0),

(508, 1,   'PI', 10.0),
(509, 5,   'PI', 9.0),
(510, 4,   'PI', 11.0);

-- =====================================================
-- EQUIPMENT and USES
-- (EID, EType, EName, Status, PDate)
-- =====================================================
INSERT INTO EQUIPMENT (EID, EType, EName, Status, PDate) VALUES
(801, 'Computing', 'NVIDIA H100 GPU Server', 'Active', '2024-01-15'),
(802, 'Robotics',  'DJI Matrice Drone',       'Active', '2024-02-20'),
(803, 'Sensor',    'LIDAR Scanner',           'Maintenance', '2023-11-10'),
(804, 'Computing', 'MacBook Pro Lab 01',      'Active', '2023-05-05'),
(805, 'Measurement','High-Precision Oscilloscope','Active','2024-09-01');

INSERT INTO USES (MID, EID, SDate, EDate, Purpose) VALUES
(10, 801, '2025-11-01', '2026-05-30', 'Training AI Models'),
(11, 802, '2025-10-15', '2025-12-20', 'Drone Flight Testing'),
(12, 804, '2024-01-01', '2024-06-01', 'Thesis Writing'),
(15, 805, '2025-02-01', '2025-04-01', 'Signal Measurements');

-- =====================================================
-- PUBLICATIONS / PUBLISHES
-- (PUBLICATION: PubID, Title, Venue, Date, DOI)
-- (PUBLISHES: MID, PubID, SDate, EDate, Purpose)
-- =====================================================
INSERT INTO PUBLICATION (PubID, Title, Venue, Date, DOI) VALUES
(901, 'Advances in Drone AI',           'IEEE Robotics',   '2024-03-15', '10.1109/robot.2024'),
(902, 'Legal NLP Systems',              'ACL Conference',  '2024-07-20', '10.1145/acl.2024'),
(903, 'Optimizing Neural Networks',     'NeurIPS',         '2024-12-01', '10.1109/nips.2024'),
(904, 'Data Trends in 2025',            'Nature',          '2025-01-10', '10.1038/data.2025'),
(905, 'Quantum Error Correction',       'Phys. Rev. X',    '2023-11-15', '10.1103/prx.2023'),
(906, 'Pending Research Study',         'ArXiv',           '2025-02-01', NULL),
(907, 'Edge AI Benchmarking',           'Sensors Journal', '2024-11-10', '10.3390/sensors.2024'),
(908, 'Bioinformatics Pipelines',       'BMC Bioinformatics','2025-01-05', '10.1186/bmc.2025');

INSERT INTO PUBLISHES (MID, PubID, SDate, EDate, Purpose) VALUES
(1,   901, '2023-06-01', '2024-03-15', 'Primary Author'),
(10,  901, '2023-06-01', '2024-03-15', 'Co-Author'),
(2,   902, '2024-01-01', '2024-07-20', 'Primary Author'),
(12,  902, '2024-01-01', '2024-07-20', 'Researcher'),
(1,   903, '2024-08-01', '2024-12-01', 'Supervisor'),
(11,  903, '2024-08-01', '2024-12-01', 'Experiment Lead'),
(1,   905, '2023-01-01', '2023-11-15', 'Co-Author'),
(3,   906, '2024-12-01', '2025-02-01', 'Drafting'),
(16,  907, '2024-09-01', '2024-11-10', 'Benchmarking'),
(20,  908, '2024-12-01', '2025-01-05', 'Primary Author');

SET FOREIGN_KEY_CHECKS = 1;
