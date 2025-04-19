-- Create Events table
CREATE TABLE Events (
    event_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    location VARCHAR(200) NOT NULL,
    capacity INT NOT NULL,
    organizer_id INT NOT NULL
);

-- Create Organizers table
CREATE TABLE Organizers (
    organizer_id INT PRIMARY KEY AUTO_INCREMENT,
    club_name VARCHAR(100) NOT NULL,
    contact_email VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL
);

-- Create Students table
CREATE TABLE Students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    roll_number VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE
);

-- Create Registrations table
CREATE TABLE Registrations (
    registration_id INT PRIMARY KEY AUTO_INCREMENT,
    event_id INT NOT NULL,
    student_id INT NOT NULL,
    registration_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES Events(event_id),
    FOREIGN KEY (student_id) REFERENCES Students(student_id)
);

-- Create Feedback table
CREATE TABLE Feedback (
    feedback_id INT PRIMARY KEY AUTO_INCREMENT,
    event_id INT NOT NULL,
    student_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    FOREIGN KEY (event_id) REFERENCES Events(event_id),
    FOREIGN KEY (student_id) REFERENCES Students(student_id)
);

-- Add foreign key to Events table after Organizers table is created
ALTER TABLE Events
ADD FOREIGN KEY (organizer_id) REFERENCES Organizers(organizer_id);

-- Example JOIN Query: Get event details with organizer information
SELECT 
    e.title,
    e.event_date,
    e.event_time,
    e.location,
    o.club_name,
    o.contact_email
FROM Events e
JOIN Organizers o ON e.organizer_id = o.organizer_id;

-- Example Subquery: Find events with more than 50 registrations
SELECT 
    e.title,
    e.event_date,
    COUNT(r.registration_id) as registration_count
FROM Events e
JOIN Registrations r ON e.event_id = r.event_id
GROUP BY e.event_id
HAVING registration_count > 50;

-- Trigger to update event capacity when a new registration is added
DELIMITER //
CREATE TRIGGER after_registration_insert
AFTER INSERT ON Registrations
FOR EACH ROW
BEGIN
    UPDATE Events 
    SET capacity = capacity - 1
    WHERE event_id = NEW.event_id;
END//
DELIMITER ; 