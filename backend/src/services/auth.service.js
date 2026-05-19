const crypto = require('crypto');
const { query } = require('../config/db');
const env = require('../config/env');

const TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60;

function normalizeEmail(email) {
  return String(email || '').trim().toLowerCase();
}

function validateCredentials({ name, email, password }, requireName = false) {
  if (requireName && !String(name || '').trim()) {
    throw new Error('Name is required');
  }
  if (!normalizeEmail(email)) {
    throw new Error('Email is required');
  }
  if (!password || password.length < 6) {
    throw new Error('Password must be at least 6 characters');
  }
}

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(password, storedHash) {
  const [salt, hash] = String(storedHash || '').split(':');
  if (!salt || !hash) return false;

  const candidate = crypto.scryptSync(password, salt, 64);
  const stored = Buffer.from(hash, 'hex');
  return stored.length === candidate.length && crypto.timingSafeEqual(stored, candidate);
}

function base64Url(input) {
  return Buffer.from(JSON.stringify(input)).toString('base64url');
}

function signToken(user) {
  const header = base64Url({ alg: 'HS256', typ: 'JWT' });
  const payload = base64Url({
    sub: user.id,
    email: user.email,
    name: user.name,
    exp: Math.floor(Date.now() / 1000) + TOKEN_TTL_SECONDS,
  });
  const signature = crypto
    .createHmac('sha256', env.JWT_SECRET)
    .update(`${header}.${payload}`)
    .digest('base64url');

  return `${header}.${payload}.${signature}`;
}

function verifyToken(token) {
  const [header, payload, signature] = String(token || '').split('.');
  if (!header || !payload || !signature) {
    throw new Error('Invalid token');
  }

  const expectedSignature = crypto
    .createHmac('sha256', env.JWT_SECRET)
    .update(`${header}.${payload}`)
    .digest('base64url');

  const expected = Buffer.from(expectedSignature);
  const actual = Buffer.from(signature);
  if (expected.length !== actual.length || !crypto.timingSafeEqual(expected, actual)) {
    throw new Error('Invalid token');
  }

  const decoded = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8'));
  if (decoded.exp && decoded.exp < Math.floor(Date.now() / 1000)) {
    throw new Error('Token expired');
  }
  return decoded;
}

function publicUser(row) {
  return {
    id: row.id,
    name: row.name,
    email: row.email,
    role: row.role,
    createdAt: row.created_at,
  };
}

exports.signup = async ({ name, email, password }) => {
  validateCredentials({ name, email, password }, true);

  const normalizedEmail = normalizeEmail(email);
  const existing = await query('SELECT id FROM users WHERE email = $1', [normalizedEmail]);
  if (existing.rowCount > 0) {
    throw new Error('Email is already registered');
  }

  const passwordHash = hashPassword(password);
  const result = await query(
    `INSERT INTO users (name, email, password_hash)
     VALUES ($1, $2, $3)
     RETURNING id, name, email, role, created_at`,
    [String(name).trim(), normalizedEmail, passwordHash]
  );

  const user = publicUser(result.rows[0]);
  return { user, token: signToken(user) };
};

exports.login = async ({ email, password }) => {
  validateCredentials({ email, password });

  const result = await query(
    'SELECT id, name, email, password_hash, role, created_at FROM users WHERE email = $1',
    [normalizeEmail(email)]
  );

  if (result.rowCount === 0 || !verifyPassword(password, result.rows[0].password_hash)) {
    throw new Error('Invalid email or password');
  }

  const user = publicUser(result.rows[0]);
  return { user, token: signToken(user) };
};

exports.getUserFromToken = async (token) => {
  const payload = verifyToken(token);
  const result = await query(
    'SELECT id, name, email, role, created_at FROM users WHERE id = $1',
    [payload.sub]
  );
  if (result.rowCount === 0) {
    throw new Error('User not found');
  }
  return publicUser(result.rows[0]);
};
