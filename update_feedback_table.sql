-- Check if feedback_date column exists in Feedback table
SELECT COUNT(*) INTO @exists 
FROM information_schema.columns 
WHERE table_schema = 'event_management' 
AND table_name = 'Feedback' 
AND column_name = 'feedback_date';

-- Add feedback_date column if it doesn't exist
SET @query = IF(@exists = 0, 
    'ALTER TABLE Feedback ADD COLUMN feedback_date DATETIME DEFAULT CURRENT_TIMESTAMP',
    'SELECT "feedback_date column already exists"');

PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Insert sample feedback data if none exists
INSERT INTO Feedback (event_id, student_id, rating, comment, feedback_date)
SELECT 
    e.event_id,
    s.student_id,
    FLOOR(1 + RAND() * 5) as rating,
    CONCAT('This was a ', 
           CASE FLOOR(1 + RAND() * 5)
               WHEN 1 THEN 'poor'
               WHEN 2 THEN 'fair'
               WHEN 3 THEN 'good'
               WHEN 4 THEN 'very good'
               ELSE 'excellent'
           END,
           ' event!') as comment,
    NOW() - INTERVAL FLOOR(RAND() * 30) DAY as feedback_date
FROM Events e
JOIN Students s
WHERE NOT EXISTS (
    SELECT 1 FROM Feedback f 
    WHERE f.event_id = e.event_id AND f.student_id = s.student_id
)
LIMIT 10; 