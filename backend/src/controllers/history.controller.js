const historyService = require('../services/history.service');
const { sendSuccess, sendError } = require('../utils/response');

exports.listHistory = async (req, res) => {
  try {
    const history = await historyService.listHistory(req.user.id);
    sendSuccess(res, history, 'History retrieved');
  } catch (error) {
    sendError(res, error.message, 500);
  }
};

exports.createHistory = async (req, res) => {
  try {
    const historyItem = await historyService.createHistory(req.user.id, req.body);
    sendSuccess(res, historyItem, 'History saved', 201);
  } catch (error) {
    sendError(res, error.message, 500);
  }
};

exports.deleteHistory = async (req, res) => {
  try {
    const deleted = await historyService.deleteHistory(req.user.id, req.params.id);
    if (!deleted) {
      return sendError(res, 'History item not found', 404);
    }
    sendSuccess(res, { id: req.params.id }, 'History deleted');
  } catch (error) {
    sendError(res, error.message, 500);
  }
};
