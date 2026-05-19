const authService = require('../services/auth.service');
const { sendSuccess, sendError } = require('../utils/response');

exports.signup = async (req, res) => {
  try {
    const result = await authService.signup(req.body);
    sendSuccess(res, result, 'Account created successfully', 201);
  } catch (error) {
    const statusCode = error.message.includes('already registered') ? 409 : 400;
    sendError(res, error.message, statusCode);
  }
};

exports.login = async (req, res) => {
  try {
    const result = await authService.login(req.body);
    sendSuccess(res, result, 'Logged in successfully');
  } catch (error) {
    sendError(res, error.message, 401);
  }
};

exports.me = async (req, res) => {
  try {
    const header = req.headers.authorization || '';
    const token = header.startsWith('Bearer ') ? header.slice(7) : null;
    if (!token) {
      return sendError(res, 'Missing authorization token', 401);
    }

    const user = await authService.getUserFromToken(token);
    sendSuccess(res, { user }, 'User retrieved');
  } catch (error) {
    sendError(res, error.message, 401);
  }
};
