const fs = require('fs/promises');
const path = require('path');
const env = require('../config/env');

const OCR_TIMEOUT_MS = 30 * 60 * 1000;

async function postFileToOcr(file) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), OCR_TIMEOUT_MS);

  try {
    const buffer = await fs.readFile(file.path);
    const form = new FormData();
    const blob = new Blob([buffer], { type: file.mimetype });
    form.append('file', blob, file.originalname || path.basename(file.path));

    const response = await fetch(`${env.OCR_SERVICE_URL}/ocr/extract`, {
      method: 'POST',
      body: form,
      signal: controller.signal,
    });

    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      const message = payload?.error || payload?.message || 'OCR service returned an error';
      throw new Error(message);
    }

    return payload;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('OCR service timed out while scanning the bank statement');
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

exports.extractTransactions = async (file) => {
  try {
    const result = await postFileToOcr(file);

    return {
      document: {
        fileName: file.originalname,
        storedName: file.filename,
        mimeType: file.mimetype,
        size: file.size,
      },
      summary: result.summary,
      transactions: result.transactions || [],
      rawText: result.raw_text || '',
      pages: result.pages || [],
      metadata: result.metadata || {}, // Pass through extracted metadata
      status: 'processed',
    };
  } catch (error) {
    if (error.message === 'fetch failed' || error.cause?.code === 'ECONNREFUSED') {
      throw new Error(
        `OCR service is not running at ${env.OCR_SERVICE_URL}. Start the OCR service before uploading statements.`
      );
    }

    throw new Error(`PaddleOCR extraction failed: ${error.message}`);
  }
};

exports.health = async () => {
  const response = await fetch(`${env.OCR_SERVICE_URL}/health`);
  if (!response.ok) {
    throw new Error('OCR service health check failed');
  }
  return response.json();
};
