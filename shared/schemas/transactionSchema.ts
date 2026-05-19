/**
 * Transaction Schema
 * Validation schema for transaction data
 */

export interface TransactionSchema {
  id?: string;
  date: string;
  description: string;
  debit?: number;
  credit?: number;
  balance?: number;
  type: string;
  reference?: string;
  status?: string;
  createdAt?: string;
  updatedAt?: string;
}

export const validateTransaction = (data: any): TransactionSchema => {
  if (!data.date || !data.description) {
    throw new Error('Transaction must have date and description');
  }

  if (!data.debit && !data.credit) {
    throw new Error('Transaction must have either debit or credit amount');
  }

  return {
    date: data.date,
    description: data.description,
    debit: data.debit,
    credit: data.credit,
    balance: data.balance,
    type: data.type || 'OTHER',
    reference: data.reference,
    status: data.status || 'COMPLETED',
  };
};
