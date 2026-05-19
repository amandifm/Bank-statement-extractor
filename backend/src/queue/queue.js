// Queue setup
const Queue = require('bull');
const redis = require('../config/redis');

const uploadQueue = new Queue('upload', {
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
  },
});

const ocrQueue = new Queue('ocr', {
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
  },
});

module.exports = {
  uploadQueue,
  ocrQueue,
};
