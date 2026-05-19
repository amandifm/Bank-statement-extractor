/**
 * Shared Transaction Types
 * Used across frontend, backend, and OCR service
 */

export interface Transaction {
  id: string;
  date: Date;
  description: string;
  debit?: number;
  credit?: number;
  balance?: number;
  type: string;
  reference?: string;
  status: string;
  uploadId?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface BankStatement {
  id: string;
  fileName: string;
  accountNumber?: string;
  bankName?: string;
  startDate?: Date;
  endDate?: Date;
  totalTransactions: number;
  processedAt: Date;
  status: 'PROCESSING' | 'COMPLETED' | 'FAILED';
  transactions: Transaction[];
  createdAt: Date;
}

export interface Upload {
  id: string;
  fileName: string;
  fileSize: number;
  mimeType: string;
  uploadedAt: Date;
  processedAt?: Date;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  errorMessage?: string;
}

export interface ExtractionResult {
  success: boolean;
  transactions: Transaction[];
  metadata?: {
    pageCount?: number;
    extractedAt?: Date;
    confidence?: number;
  };
  error?: string;
}
