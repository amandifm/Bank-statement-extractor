// Upload service
const ocrService = require('./ocr.service');
const transactionService = require('./transaction.service');

const uploadStatuses = new Map();

exports.processUpload = async (file) => {
  const fileId = file.filename;
  uploadStatuses.set(fileId, {
    fileId,
    status: 'processing',
    originalName: file.originalname,
    createdAt: new Date().toISOString(),
  });

  try {
    const extractedData = await ocrService.extractTransactions(file);
    transactionService.replaceTransactions(extractedData.transactions);

    const result = {
      fileId,
      originalName: file.originalname,
      status: 'processed',
      summary: extractedData.summary,
      transactions: extractedData.transactions,
      rawText: extractedData.rawText,
      document: extractedData.document,
      metadata: extractedData.metadata || {}, // Include extracted metadata
      revenueAnalysis: extractedData.revenueAnalysis || {},
    };

    uploadStatuses.set(fileId, {
      ...uploadStatuses.get(fileId),
      status: 'completed',
      completedAt: new Date().toISOString(),
      summary: extractedData.summary,
      transactionCount: extractedData.transactions.length,
    });

    return result;
  } catch (error) {
    uploadStatuses.set(fileId, {
      ...uploadStatuses.get(fileId),
      status: 'failed',
      error: error.message,
      completedAt: new Date().toISOString(),
    });
    throw new Error(`Upload processing failed: ${error.message}`);
  }
};

exports.getUploadStatus = async (fileId) => {
  try {
    const status = uploadStatuses.get(fileId);
    if (!status) {
      throw new Error('Upload not found');
    }
    return status;
  } catch (error) {
    throw new Error(`Failed to get upload status: ${error.message}`);
  }
};
