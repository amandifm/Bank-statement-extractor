// Upload controller
const uploadService = require('../services/upload.service');
const ocrService = require('../services/ocr.service');
const { sendSuccess, sendError } = require('../utils/response');

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
