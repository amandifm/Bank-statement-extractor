// Upload routes
const express = require('express');
const router = express.Router();
const uploadController = require('../controllers/upload.controller');
const uploadMiddleware = require('../middlewares/upload.middleware');

router.post('/upload', uploadMiddleware.single('file'), uploadController.uploadFile);
router.get('/upload/:id', uploadController.getUploadStatus);
router.get('/ocr/health', uploadController.ocrHealth);

module.exports = router;
