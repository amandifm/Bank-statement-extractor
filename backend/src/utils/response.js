// Response utility
exports.sendSuccess = (res, data, message = 'Success', statusCode = 200) => {
  res.status(statusCode).json({
    success: true,
    message,
    data,
  });
};

exports.sendError = (res, message = 'Error', statusCode = 400, data = null) => {
  res.status(statusCode).json({
    success: false,
    message,
    data,
  });
};

exports.sendPaginated = (res, data, page, limit, total, message = 'Success') => {
  res.status(200).json({
    success: true,
    message,
    data,
    pagination: {
      page,
      limit,
      total,
      pages: Math.ceil(total / limit),
    },
  });
};
