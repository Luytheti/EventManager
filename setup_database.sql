-- Create the database
CREATE DATABASE IF NOT EXISTS event_management;
USE event_management;

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
    contact_email VARCHAR(100) NOT NULL UNIQUE,
    contact_phone VARCHAR(20) NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Create Students table
CREATE TABLE Students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    roll_number VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
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

-- Insert sample data with passwords (using simple passwords for demo)
INSERT INTO Organizers (club_name, contact_email, contact_phone, password) VALUES
('Computer Science Club', 'csclub@university.edu', '123-456-7890', 'password123'),
('Art Society', 'artsociety@university.edu', '123-456-7891', 'password123');

INSERT INTO Students (name, roll_number, email, password) VALUES
('John Doe', 'CS001', 'john.doe@university.edu', 'password123'),
('Jane Smith', 'CS002', 'jane.smith@university.edu', 'password123');

INSERT INTO Events (title, event_date, event_time, location, capacity, organizer_id) VALUES
('Python Workshop', '2024-03-20', '14:00:00', 'Room 101', 30, 1),
('Art Exhibition', '2024-03-25', '15:00:00', 'Gallery Hall', 50, 2); 