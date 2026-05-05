### DATA INSERTION

INSERT INTO User (UserID, Email, Password, Role) VALUES 
(1, 'luvya@test.com', 'pass', 'Student'),
(2, 'madhav@test.com', 'pass', 'Student'),
(3, 'arsh@test.com', 'pass', 'Student'),
(4, 'techcorp@test.com', 'pass', 'Employer');

INSERT INTO Student (StudentID, UserID, FirstName, LastName, City, Zipcode, ReliabilityScore) VALUES 
(1, 1, 'Luvya', 'Nishad', 'Noida', '201301', 4.50),
(2, 2, 'Madhav', 'Gautam', 'Gurugram', '122001', 4.80),
(3, 3, 'Arsh', 'Ahluwalia', 'Ghaziabad', '201001', 4.20);

INSERT INTO Employer (EmployerID, UserID, BusinessName, VerifiedIdentity, TrustScore) VALUES 
(1, 4, 'TechCorp', 'Y', 4.20);

INSERT INTO Opportunity (OppID, RoleTitle, Type, Status, Description) VALUES 
(1, 'Frontend Dev', 'Freelance', 'Active', 'React project'),
(2, 'Backend Dev', 'Part-time', 'Pending', 'Node API');

INSERT INTO Posts (EmployerID, OppID) VALUES 
(1, 1), 
(1, 2);

INSERT INTO Application (ApplicationID, ApplicationDate, Status) VALUES 
(100, '2026-04-09', 'Pending'),
(200, '2026-04-09', 'Pending');

INSERT INTO Job_application (StudentID, ApplicationID, OppID) VALUES 
(1, 100, 1),
(2, 200, 2);

INSERT INTO ProjWallet (OppID, TotalAmount, Status) VALUES 
(1, 1000.00, 'Funded');


-- we can execute and see the effect of non conflicitng and conflicting transactions by running them on two seperate sql shells in given order
-- for non conflicting transactions we can run them in any schedule as they are conflict equivalent to the purely serial schedule

### NON-CONFLICTING TRANSACTIONS

### Transaction Pair 1

-- T1
START TRANSACTION;
UPDATE Student SET City = 'Faridabad' WHERE StudentID = 1;
UPDATE Student SET Zipcode = '121001' WHERE StudentID = 1;
COMMIT;

-- T2
START TRANSACTION;
UPDATE Employer SET BusinessName = 'TechCorp Global' WHERE EmployerID = 1;
UPDATE Employer SET TrustScore = 4.50 WHERE EmployerID = 1;
COMMIT;


### Transaction Pair 2

-- T1
START TRANSACTION;
INSERT INTO Application (ApplicationID, ApplicationDate, Status) VALUES (300, CURDATE(), 'Pending');
INSERT INTO Job_application (StudentID, ApplicationID, OppID) VALUES (2, 300, 2);
COMMIT;

-- T2
START TRANSACTION;
INSERT INTO SkillTags (StudentID, Skill) VALUES (3, 'Python');
INSERT INTO SkillTags (StudentID, Skill) VALUES (3, 'Django');
COMMIT;


### Transaction Pair 3

-- T1
START TRANSACTION;
INSERT INTO MilestoneLedger (OppID, Payout, ApprovalStatus) VALUES (1, 250.00, 'Pending');
UPDATE Opportunity SET Status = 'Funded' WHERE OppID = 1;
COMMIT;

-- T2
START TRANSACTION;
INSERT INTO MilestoneLedger (OppID, Payout, ApprovalStatus) VALUES (2, 400.00, 'Pending');
UPDATE Opportunity SET Status = 'Active' WHERE OppID = 2;
COMMIT;


### Transaction Pair 4

-- T1
START TRANSACTION;
SELECT * FROM Application WHERE Status = 'Pending';
SELECT * FROM Opportunity WHERE Status = 'Pending';
COMMIT;

-- T2
START TRANSACTION;
INSERT INTO Interview (ApplicationID, ScheduledTime, MeetingType, ApplicationStatus) VALUES (100, '2026-05-01 10:00:00', 'Zoom', 'Scheduled');
UPDATE Application SET Status = 'Accepted' WHERE ApplicationID = 100;
COMMIT;


### CONFLICTING TRANSACTIONS

### Transaction Pair 5: WW conflict

-- T1
START TRANSACTION;
UPDATE ProjWallet SET TotalAmount = TotalAmount - 50 WHERE OppID = 1; -- 1
UPDATE ProjWallet SET Status = 'Released' WHERE OppID = 1; -- 3
COMMIT; -- 4

-- T2
START TRANSACTION;
UPDATE ProjWallet SET TotalAmount = TotalAmount - 100 WHERE OppID = 1; -- 2 
UPDATE ProjWallet SET Status = 'Escrow' WHERE OppID = 1; -- 5
COMMIT; -- 6


### Transaction Pair 6: WR conflict

-- T1
START TRANSACTION;
UPDATE Student SET ReliabilityScore = 2.50 WHERE StudentID = 2; -- 1
UPDATE Student SET City = 'Delhi' WHERE StudentID = 2; -- 3
COMMIT; -- 4

-- T2
START TRANSACTION;
SELECT ReliabilityScore FROM Student WHERE StudentID = 2; -- 2 
SELECT City FROM Student WHERE StudentID = 2; -- 5
COMMIT; -- 6


### Transaction Pair 7: RW conflict

-- T1
START TRANSACTION;
SELECT Description FROM Opportunity WHERE OppID = 1; -- 1
SELECT RoleTitle FROM Opportunity WHERE OppID = 1; -- 3
COMMIT; -- 4

-- T2
START TRANSACTION;
UPDATE Opportunity SET Description = 'Must know React hooks' WHERE OppID     = 1; -- 2 
UPDATE Opportunity SET RoleTitle = 'Senior Frontend Dev' WHERE OppID = 1; -- 5
COMMIT; -- 6    