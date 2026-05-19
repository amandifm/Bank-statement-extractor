#!/usr/bin/env node
/**
 * Backend Diagnostics Script
 * Checks connectivity and configuration
 */

const http = require('http');
const { Pool } = require('pg');
require('dotenv').config();

const tests = [];

// Helper function to make HTTP requests
function httpRequest(options) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, data }));
    });
    req.on('error', reject);
    req.end();
  });
}

// Test 1: OCR Service Health
async function testOCRHealth() {
  try {
    const result = await httpRequest({
      hostname: 'localhost',
      port: 8000,
      path: '/ocr/health',
      method: 'GET',
      timeout: 5000,
    });
    
    if (result.status === 200) {
      tests.push({ name: 'OCR Service Health', status: '✓ OK' });
    } else {
      tests.push({ name: 'OCR Service Health', status: `✗ Status ${result.status}` });
    }
  } catch (error) {
    tests.push({ name: 'OCR Service Health', status: `✗ ${error.message}` });
  }
}

// Test 2: PostgreSQL Connection
async function testPostgres() {
  const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME || 'bank_extractor',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'password',
  });

  try {
    const client = await pool.connect();
    await client.query('SELECT 1');
    client.release();
    tests.push({ name: 'PostgreSQL Connection', status: '✓ OK' });
  } catch (error) {
    tests.push({ name: 'PostgreSQL Connection', status: `✗ ${error.message}` });
  } finally {
    await pool.end();
  }
}

// Test 3: Redis Connection
async function testRedis() {
  try {
    // Simple connection test without requiring redis library
    const net = require('net');
    const socket = net.createConnection({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      timeout: 3000,
    });

    socket.on('connect', () => {
      tests.push({ name: 'Redis Connection', status: '✓ OK' });
      socket.destroy();
    });

    socket.on('error', (error) => {
      tests.push({ name: 'Redis Connection', status: `✗ ${error.message}` });
    });

    await new Promise(resolve => setTimeout(resolve, 3500));
  } catch (error) {
    tests.push({ name: 'Redis Connection', status: `✗ ${error.message}` });
  }
}

// Test 4: Check Environment Configuration
function testEnvironment() {
  const required = [
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'OCR_SERVICE_URL',
  ];

  let missing = [];
  for (const key of required) {
    if (!process.env[key]) {
      missing.push(key);
    }
  }

  if (missing.length === 0) {
    tests.push({ name: 'Environment Variables', status: '✓ All required set' });
  } else {
    tests.push({ name: 'Environment Variables', status: `✗ Missing: ${missing.join(', ')}` });
  }
}

// Main test runner
async function runTests() {
  console.log('\n' + '='.repeat(60));
  console.log('🔍 Backend Diagnostics');
  console.log('='.repeat(60) + '\n');

  testEnvironment();
  await testOCRHealth();
  await testPostgres();
  await testRedis();

  // Print results
  console.log('Test Results:');
  console.log('-'.repeat(60));
  for (const test of tests) {
    console.log(`${test.name.padEnd(30)} ${test.status}`);
  }
  console.log('-'.repeat(60));

  const failed = tests.filter(t => t.status.includes('✗')).length;
  if (failed === 0) {
    console.log('\n✓ All checks passed!');
  } else {
    console.log(`\n⚠ ${failed} check(s) failed. See above for details.`);
  }

  console.log('='.repeat(60) + '\n');

  process.exit(failed > 0 ? 1 : 0);
}

runTests().catch(error => {
  console.error('Diagnostics failed:', error);
  process.exit(1);
});
