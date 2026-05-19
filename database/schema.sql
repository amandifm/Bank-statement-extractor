-- Bank Statement Extractor Database Schema
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'user',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- User scan history table
CREATE TABLE IF NOT EXISTS scan_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  file_name VARCHAR(255) NOT NULL,
  transaction_count INTEGER NOT NULL DEFAULT 0,
  average_confidence NUMERIC(5, 4),
  transactions JSONB NOT NULL DEFAULT '[]'::jsonb,
  summary JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scan_history_user_id ON scan_history(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_history_created_at ON scan_history(created_at);

-- Uploads table
CREATE TABLE IF NOT EXISTS uploads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  file_name VARCHAR(255) NOT NULL,
  file_size INTEGER,
  mime_type VARCHAR(50),
  status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, FAILED
  error_message TEXT,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  processed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Bank Statements table
CREATE TABLE IF NOT EXISTS bank_statements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id UUID NOT NULL REFERENCES uploads(id),
  account_number VARCHAR(100),
  bank_name VARCHAR(255),
  start_date DATE,
  end_date DATE,
  total_transactions INTEGER DEFAULT 0,
  status VARCHAR(50) DEFAULT 'PROCESSING', -- PROCESSING, COMPLETED, FAILED
  processed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bank_statement_id UUID NOT NULL REFERENCES bank_statements(id),
  transaction_date DATE NOT NULL,
  description VARCHAR(500),
  debit DECIMAL(12, 2),
  credit DECIMAL(12, 2),
  balance DECIMAL(12, 2),
  transaction_type VARCHAR(50), -- DEPOSIT, WITHDRAWAL, TRANSFER, etc.
  reference_number VARCHAR(100),
  status VARCHAR(50) DEFAULT 'COMPLETED', -- PENDING, COMPLETED, FAILED
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (bank_statement_id) REFERENCES bank_statements(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_uploads_user_id ON uploads(user_id);
CREATE INDEX idx_uploads_status ON uploads(status);
CREATE INDEX idx_bank_statements_upload_id ON bank_statements(upload_id);
CREATE INDEX idx_transactions_bank_statement_id ON transactions(bank_statement_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
