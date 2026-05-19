// Environment configuration
require('dotenv').config();

module.exports = {
  NODE_ENV: process.env.NODE_ENV || 'development',
  PORT: process.env.API_PORT || process.env.PORT || 5000,
  MONGODB_URI: process.env.MONGODB_URI,
  REDIS_HOST: process.env.REDIS_HOST || 'localhost',
  REDIS_PORT: process.env.REDIS_PORT || 6379,
  OCR_SERVICE_URL: process.env.OCR_SERVICE_URL || 'http://localhost:8000',
  JWT_SECRET: process.env.JWT_SECRET || 'change-this-local-secret',
};
