// Transaction routes
const express = require('express');
const router = express.Router();
const transactionController = require('../controllers/transaction.controller');

router.get('/transactions', transactionController.getTransactions);
router.get('/transactions/:id', transactionController.getTransactionById);
router.post('/transactions', transactionController.createTransaction);
router.put('/transactions/:id', transactionController.updateTransaction);

module.exports = router;
