-- Create ConflictAlerts table
CREATE TABLE IF NOT EXISTS ConflictAlerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT,
    student_id INT,
    conflict_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES Events(event_id),
    FOREIGN KEY (student_id) REFERENCES Students(student_id)
);

-- Create EventDateConflicts table
CREATE TABLE IF NOT EXISTS EventDateConflicts (
    conflict_id INT AUTO_INCREMENT PRIMARY KEY,
    event_date DATE NOT NULL,
    existing_event_id INT,
    new_event_id INT,
    conflict_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (existing_event_id) REFERENCES Events(event_id),
    FOREIGN KEY (new_event_id) REFERENCES Events(event_id)
);

-- Capacity check trigger
DELIMITER $$

CREATE TRIGGER check_capacity
BEFORE INSERT ON Registrations
FOR EACH ROW
BEGIN
    DECLARE available_capacity INT;
    
    -- Get the current number of registrations for the event
    SELECT capacity - (SELECT COUNT(*) 
                       FROM Registrations 
                       WHERE event_id = NEW.event_id) 
    INTO available_capacity
    FROM Events 
    WHERE event_id = NEW.event_id;
    
    -- If no capacity is available, raise a custom error
    IF available_capacity <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sorry, this event is fully booked. Better luck next year!';
    END IF;
END $$

-- Event date conflict check trigger
CREATE TRIGGER check_event_date_conflict
BEFORE INSERT ON Events
FOR EACH ROW
BEGIN
    DECLARE existing_event_count INT;
    DECLARE existing_event_id INT;
    
    -- Check for existing events on the same date
    SELECT COUNT(*), MAX(event_id)
    INTO existing_event_count, existing_event_id
    FROM Events
    WHERE event_date = NEW.event_date;
    
    -- If there's an existing event, log the conflict
    IF existing_event_count > 0 THEN
        INSERT INTO EventDateConflicts (event_date, existing_event_id, new_event_id)
        VALUES (NEW.event_date, existing_event_id, NEW.event_id);
        
        -- Raise a custom error with the existing event ID
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = CONCAT('An event already exists on this date. Existing event ID: ', existing_event_id);
    END IF;
END $$



-- Delete feedback on event cancellation
CREATE TRIGGER delete_feedback_on_event_cancel
AFTER UPDATE ON Events
FOR EACH ROW
BEGIN
    -- Check if the event's status changed to 'canceled' 
    IF OLD.status != 'canceled' AND NEW.status = 'canceled' THEN
        DELETE FROM Feedback WHERE event_id = NEW.event_id;
    END IF;
END $$

-- Delete feedback on unregister
CREATE TRIGGER delete_feedback_on_unregister
AFTER DELETE ON Registrations
FOR EACH ROW
BEGIN
    DELETE FROM Feedback
    WHERE student_id = OLD.student_id AND event_id = OLD.event_id;
END $$

-- Update event capacity
CREATE TRIGGER update_event_capacity
AFTER INSERT ON Registrations
FOR EACH ROW
BEGIN
    UPDATE Events
    SET capacity = capacity - 1
    WHERE event_id = NEW.event_id;
END $$



-- Cleanup on event deletion
CREATE TRIGGER cleanup_on_event_delete
BEFORE DELETE ON Events
FOR EACH ROW
BEGIN
    -- Delete all registrations for the event
    DELETE FROM Registrations WHERE event_id = OLD.event_id;
    
    -- Delete all feedback for the event
    DELETE FROM Feedback WHERE event_id = OLD.event_id;
    
    -- Delete any conflict alerts for the event
    DELETE FROM ConflictAlerts WHERE event_id = OLD.event_id;
    
    -- Delete any date conflicts for the event
    DELETE FROM EventDateConflicts 
    WHERE existing_event_id = OLD.event_id OR new_event_id = OLD.event_id;
END $$

DELIMITER ; 