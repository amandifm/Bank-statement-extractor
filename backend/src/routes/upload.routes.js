// Upload routes
const express = require('express');
const router = express.Router();
const uploadController = require('../controllers/upload.controller');
const uploadMiddleware = require('../middlewares/upload.middleware');

// Single file
router.post('/upload', uploadMiddleware.single('file'), uploadController.uploadFile);

// Batch — up to 10 files, field name "files"
router.post('/upload-batch', uploadMiddleware.array('files', 10), uploadController.uploadBatch);

router.get('/upload/:id', uploadController.getUploadStatus);
router.get('/ocr/health', uploadController.ocrHealth);

module.exports = router;