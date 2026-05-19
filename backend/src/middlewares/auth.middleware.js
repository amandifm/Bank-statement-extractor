const authService = require('../services/auth.service');

module.exports = async (req, res, next) => {
  try {
    const header = req.headers.authorization || '';
    const token = header.startsWith('Bearer ') ? header.slice(7) : null;

    if (!token) {
      return res.status(401).json({ success: false, message: 'Missing authorization token' });
    }

    req.user = await authService.getUserFromToken(token);
    next();
  } catch (error) {
    res.status(401).json({ success: false, message: error.message });
  }
};
