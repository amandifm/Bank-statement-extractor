-- Seed data for Bank Statement Extractor

-- Insert sample user (password would be hashed in real application)
INSERT INTO users (email, name) VALUES
('demo@example.com', 'Demo User'),
('test@example.com', 'Test User')
ON CONFLICT (email) DO NOTHING;

-- Insert sample transaction types (if using enum)
-- These are just reference data that might be useful

-- Example: Sample upload (would be created through API)
-- INSERT INTO uploads (user_id, file_name, file_size, mime_type, status)
-- VALUES (
--   (SELECT id FROM users WHERE email = 'demo@example.com'),
--   'statement_jan_2024.pdf',
--   2048576,
--   'application/pdf',
--   'COMPLETED'
-- );
