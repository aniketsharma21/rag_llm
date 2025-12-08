const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/ws',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      ws: true,
    })
  );
  app.use(
    '/',
    createProxyMiddleware({
      target: 'http://localhost:8000',
    })
  );
};
