// File deletion utility
const fs = require('fs').promises;
const path = require('path');

exports.deleteFile = async (filePath) => {
  try {
    await fs.unlink(filePath);
    console.log(`File deleted: ${filePath}`);
  } catch (error) {
    console.error(`Failed to delete file: ${error.message}`);
    throw error;
  }
};

exports.deleteDirectory = async (dirPath) => {
  try {
    await fs.rm(dirPath, { recursive: true, force: true });
    console.log(`Directory deleted: ${dirPath}`);
  } catch (error) {
    console.error(`Failed to delete directory: ${error.message}`);
    throw error;
  }
};

exports.deleteOldFiles = async (dirPath, maxAgeMs) => {
  try {
    const files = await fs.readdir(dirPath);
    const now = Date.now();
    
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      const stats = await fs.stat(filePath);
      const age = now - stats.mtimeMs;
      
      if (age > maxAgeMs) {
        await fs.unlink(filePath);
        console.log(`Old file deleted: ${filePath}`);
      }
    }
  } catch (error) {
    console.error(`Failed to delete old files: ${error.message}`);
    throw error;
  }
};
