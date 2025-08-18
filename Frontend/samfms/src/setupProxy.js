const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  // Get WebSocket target from environment or use default
  const wsTarget = process.env.REACT_APP_WS_TARGET || 'wss://capstone-samfms.dns.net.za:21017';

  // Proxy WebSocket connections for hot module replacement
  app.use(
    '/ws',
    createProxyMiddleware({
      target: wsTarget,
      ws: true,
      changeOrigin: true,
      secure: false, // Allow self-signed certificates
      logLevel: 'info',
      onError: (err, req, res) => {
        console.error('WebSocket proxy error:', err);
      },
      onProxyReqWs: (proxyReq, req, socket) => {
        console.log('WebSocket proxy request:', req.url);
      },
    })
  );

  // Proxy API calls during development
  if (process.env.NODE_ENV === 'development') {
    const apiTarget = process.env.REACT_APP_API_BASE_URL || 'http://localhost:21004';

    app.use(
      '/api',
      createProxyMiddleware({
        target: apiTarget,
        changeOrigin: true,
        logLevel: 'info',
        onError: (err, req, res) => {
          console.error('API proxy error:', err);
        },
      })
    );
  }
};
