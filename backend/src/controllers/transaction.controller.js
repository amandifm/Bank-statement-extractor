// Transaction controller
const transactionService = require('../services/transaction.service');
const { sendSuccess, sendError } = require('../utils/response');

exports.getTransactions = async (req, res) => {
  try {
    const transactions = await transactionService.getAllTransactions();
    sendSuccess(res, transactions, 'Transactions retrieved');
  } catch (error) {
    sendError(res, error.message, 500);
  }
};

exports.getTransactionById = async (req, res) => {
  try {
    const transaction = await transactionService.getTransactionById(req.params.id);
    sendSuccess(res, transaction, 'Transaction retrieved');
  } catch (error) {
    sendError(res, error.message, 500);
  }
};

exports.createTransaction = async (req, res) => {
  try {
    const transaction = await transactionService.createTransaction(req.body);
    sendSuccess(res, transaction, 'Transaction created', 201);
  } catch (error) {
    sendError(res, error.message, 500);
  }
};

exports.updateTransaction = async (req, res) => {
  try {
    const transaction = await transactionService.updateTransaction(req.params.id, req.body);
    sendSuccess(res, transaction, 'Transaction updated');
  } catch (error) {
    sendError(res, error.message, 500);
  }
};
