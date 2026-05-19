// Queue processor
const { uploadQueue, ocrQueue } = require('./queue');
const ocrService = require('../services/ocr.service');

uploadQueue.process(async (job) => {
  try {
    console.log('Processing upload job:', job.id);
    // Process upload job
    job.progress(50);
    return { success: true, message: 'Upload processed' };
  } catch (error) {
    throw error;
  }
});

ocrQueue.process(async (job) => {
  try {
    console.log('Processing OCR job:', job.id);
    const result = await ocrService.extractText(job.data.filePath);
    job.progress(100);
    return result;
  } catch (error) {
    throw error;
  }
});

module.exports = { uploadQueue, ocrQueue };
