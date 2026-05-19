let transactions = [];

exports.replaceTransactions = (items = []) => {
  transactions = items.map((item, index) => ({
    id: item.id || `txn-${String(index + 1).padStart(4, '0')}`,
    ...item,
  }));
  return transactions;
};

exports.getAllTransactions = async () => transactions;

exports.getTransactionById = async (id) => {
  return transactions.find((transaction) => transaction.id === id) || null;
};

exports.createTransaction = async (data) => {
  const transaction = {
    id: data.id || `txn-${String(transactions.length + 1).padStart(4, '0')}`,
    ...data,
  };
  transactions.push(transaction);
  return transaction;
};

exports.updateTransaction = async (id, data) => {
  const index = transactions.findIndex((transaction) => transaction.id === id);
  if (index === -1) {
    return null;
  }
  transactions[index] = { ...transactions[index], ...data };
  return transactions[index];
};
