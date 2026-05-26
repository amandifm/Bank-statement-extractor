// Upload controller
const uploadService = require('../services/upload.service');
const ocrService = require('../services/ocr.service');
const { sendSuccess, sendError } = require('../utils/response');

// Single file upload (existing)
exports.uploadFile = async (req, res) => {
  try {
    if (!req.file) {
      return sendError(res, 'No file uploaded', 400);
    }
    const result = await uploadService.processUpload(req.file);
    sendSuccess(res, result, 'File uploaded successfully');
  } catch (error) {
    sendError(res, error.message, 500);
  }
};

// Batch upload — processes up to 10 files sequentially, streaming NDJSON results.
// Each file is fully isolated: any error (OCR timeout, corrupt PDF, network blip)
// is caught, reported, and the loop unconditionally advances to the next file.
exports.uploadBatch = async (req, res) => {
  const files = req.files;

  if (!files || files.length === 0) {
    return sendError(res, 'No files uploaded', 400);
  }

  if (files.length > 10) {
    return sendError(res, 'Maximum 10 files allowed per batch', 400);
  }

  // NDJSON stream — client reads line-by-line as each file finishes
  res.setHeader('Content-Type', 'application/x-ndjson');
  res.setHeader('Transfer-Encoding', 'chunked');
  res.setHeader('Cache-Control', 'no-cache');
  res.flushHeaders();

  const total = files.length;
  let successCount = 0;
  let failCount = 0;

  // Helper: write a JSON line; ignore write errors (client may have disconnected)
  function writeLine(obj) {
    try {
      res.write(JSON.stringify(obj) + '\n');
    } catch (_) { /* client disconnected – nothing to do */ }
  }

  for (let index = 0; index < files.length; index++) {
    const file = files[index];

    writeLine({
      event: 'file_started',
      index,
      total,
      fileName: file.originalname,
    });

    // Every file gets its own isolated try/catch.
    // Nothing inside can propagate to the outer loop.
    let result = null;
    let fileError = null;

    try {
      result = await uploadService.processUpload(file);
    } catch (err) {
      fileError = err instanceof Error ? err.message : String(err);
    }

    if (fileError) {
      failCount++;
      writeLine({
        event: 'file_done',
        index,
        total,
        fileName: file.originalname,
        success: false,
        error: fileError,
      });
    } else {
      successCount++;
      writeLine({
        event: 'file_done',
        index,
        total,
        fileName: file.originalname,
        success: true,
        data: result,
      });
    }

    // Small yield so Node can flush the chunk before starting the next OCR call
    await new Promise((resolve) => setImmediate(resolve));
  }

  writeLine({
    event: 'batch_complete',
    total,
    successCount,
    failCount,
  });

  res.end();
};

exports.ocrHealth = async (req, res) => {
  try {
    const status = await ocrService.health();
    sendSuccess(res, status, 'OCR service is healthy');
  } catch (error) {
    sendError(res, error.message, 503);
  }
};

exports.getUploadStatus = async (req, res) => {
  try {
    const status = await uploadService.getUploadStatus(req.params.id);
    sendSuccess(res, status, 'Upload status retrieved');
  } catch (error) {
    sendError(res, error.message, 500);
  }
};