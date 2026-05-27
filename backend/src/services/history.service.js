const { query } = require('../config/db');

function mapHistory(row) {
  return {
    id: row.id,
    fileName: row.file_name,
    transactionCount: row.transaction_count,
    averageConfidence: row.average_confidence,
    transactions: row.transactions,
    metadata: row.metadata,
    summary: row.summary,
    createdAt: row.created_at,
  };
}

exports.listHistory = async (userId) => {
  const result = await query(
    `SELECT id, file_name, transaction_count, average_confidence, transactions, metadata, summary, created_at
     FROM scan_history
     WHERE user_id = $1
     ORDER BY created_at DESC`,
    [userId]
  );
  return result.rows.map(mapHistory);
};

exports.createHistory = async (userId, data) => {
  const transactions = Array.isArray(data.transactions) ? data.transactions : [];
  const metadata = data.metadata || {};
  const summary = data.summary || {};
  const result = await query(
    `INSERT INTO scan_history (
      user_id,
      file_name,
      transaction_count,
      average_confidence,
      transactions,
      metadata,
      summary
    )
    VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7::jsonb)
    RETURNING id, file_name, transaction_count, average_confidence, transactions, metadata, summary, created_at`,
    [
      userId,
      data.fileName || 'Bank statement',
      transactions.length,
      summary.average_confidence || summary.averageConfidence || null,
      JSON.stringify(transactions),
      JSON.stringify(metadata),
      JSON.stringify(summary),
    ]
  );
  return mapHistory(result.rows[0]);
};

exports.deleteHistory = async (userId, historyId) => {
  const result = await query(
    'DELETE FROM scan_history WHERE id = $1 AND user_id = $2 RETURNING id',
    [historyId, userId]
  );
  return result.rowCount > 0;
};
