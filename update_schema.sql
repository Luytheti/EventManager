-- Update Events table
ALTER TABLE Events ADD COLUMN IF NOT EXISTS description TEXT;

-- Update Registrations table
ALTER TABLE Registrations ADD COLUMN IF NOT EXISTS registration_date DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Update Feedback table
ALTER TABLE Feedback ADD COLUMN IF NOT EXISTS rating INT CHECK (rating >= 1 AND rating <= 5);
ALTER TABLE Feedback ADD COLUMN IF NOT EXISTS comment TEXT; 