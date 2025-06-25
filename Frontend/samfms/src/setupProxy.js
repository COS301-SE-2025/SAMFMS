const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy WebSocket connections for hot module replacement
  app.use(
    '/ws',
    createProxyMiddleware({
      target: 'wss://capstone-samfms.dns.net.za:21024',
      ws: true,
      changeOrigin: true,
      secure: false, // Allow self-signed certificates
      logLevel: 'debug'
    })
  );
};
