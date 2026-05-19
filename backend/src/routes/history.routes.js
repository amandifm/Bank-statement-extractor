const express = require('express');
const historyController = require('../controllers/history.controller');
const requireAuth = require('../middlewares/auth.middleware');

const router = express.Router();

router.use(requireAuth);
router.get('/', historyController.listHistory);
router.post('/', historyController.createHistory);
router.delete('/:id', historyController.deleteHistory);

module.exports = router;
