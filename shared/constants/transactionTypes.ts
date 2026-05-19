/**
 * Transaction Types Constants
 * Predefined types of transactions for bank statements
 */

export const TRANSACTION_TYPES = {
  DEPOSIT: 'DEPOSIT',
  WITHDRAWAL: 'WITHDRAWAL',
  TRANSFER: 'TRANSFER',
  CHECK: 'CHECK',
  ATM_WITHDRAWAL: 'ATM_WITHDRAWAL',
  FEE: 'FEE',
  INTEREST: 'INTEREST',
  OTHER: 'OTHER',
} as const;

export const TRANSACTION_STATUS = {
  PENDING: 'PENDING',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  CANCELLED: 'CANCELLED',
} as const;

export type TransactionType = (typeof TRANSACTION_TYPES)[keyof typeof TRANSACTION_TYPES];
export type TransactionStatus = (typeof TRANSACTION_STATUS)[keyof typeof TRANSACTION_STATUS];
