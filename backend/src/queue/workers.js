// Queue workers
const { uploadQueue, ocrQueue } = require('./processor');

uploadQueue.on('completed', (job) => {
  console.log(`Upload job ${job.id} completed`);
});

uploadQueue.on('failed', (job, err) => {
  console.error(`Upload job ${job.id} failed:`, err);
});

ocrQueue.on('completed', (job) => {
  console.log(`OCR job ${job.id} completed`);
});

ocrQueue.on('failed', (job, err) => {
  console.error(`OCR job ${job.id} failed:`, err);
});

module.exports = { uploadQueue, ocrQueue };
