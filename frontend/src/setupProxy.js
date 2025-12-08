const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/ws/chat',
    createProxyMiddleware({
      target: 'http://127.0.0.1:8000',
      ws: true,
    })
  );
  app.use(
    ['/health', '/ingest', '/status', '/files', '/query', '/conversations'],
    createProxyMiddleware({
      target: 'http://127.0.0.1:8000',
    })
  );
};
