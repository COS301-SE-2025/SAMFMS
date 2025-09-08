# SAMFMS HTTPS Setup with Caddy

This setup provides automatic HTTPS for the SAMFMS application using Caddy reverse proxy with self-signed certificates for IP-based access.

## Quick Start

1. **Start the application with HTTPS:**
   ```bash
   docker compose up --build
   ```

2. **Access the application:**
   - **HTTPS (recommended):** https://localhost (port 443)
   - **HTTP (redirects to HTTPS):** http://localhost (port 80)
   - **Your server IP:** https://YOUR_SERVER_IP

## What This Setup Provides

- ✅ **Automatic HTTPS** on standard port 443
- ✅ **HTTP to HTTPS redirect** on port 80
- ✅ **Self-signed certificates** for IP-based access
- ✅ **Reverse proxy** routing to frontend and API
- ✅ **Security headers** (HSTS, XSS protection, etc.)
- ✅ **WebSocket support** for real-time features
- ✅ **API routing** under `/api/*` path

## Service Architecture

```
Internet/Browser
       ↓
Caddy (ports 80/443) - HTTPS termination & reverse proxy
       ↓
├── Frontend (React) - Serves the web application
└── Core API - Handles API requests (/api/*, /auth/*, /health/*, /ws/*)
```

## Important Notes

### Browser Security Warning
Since we're using self-signed certificates for IP access, browsers will show a security warning. This is normal and expected. You can:

1. **Click "Advanced"** then **"Proceed to localhost (unsafe)"**
2. **Add security exception** in your browser
3. **Use Chrome with flag:** `--ignore-certificate-errors-spki-list --ignore-ssl-errors`

### URL Changes
- Frontend now uses: `https://localhost/`
- API endpoints now use: `https://localhost/api/`
- WebSockets now use: `wss://localhost/ws/`

### Development vs Production
- **Development:** Uses self-signed certificates (this setup)
- **Production:** Replace IP with domain name in Caddyfile for Let's Encrypt certificates

## Troubleshooting

### Check if services are running:
```bash
docker compose ps
```

### View Caddy logs:
```bash
docker compose logs caddy
```

### View all logs:
```bash
docker compose logs
```

### Restart specific service:
```bash
docker compose restart caddy
docker compose restart frontend
docker compose restart core
```

### Test endpoints:
```bash
# Test HTTPS (ignore certificate warnings)
curl -k https://localhost

# Test API
curl -k https://localhost/api/health

# Test HTTP redirect
curl -I http://localhost
```

## Customization

### To use a custom domain instead of IP:
1. Edit `Caddyfile`
2. Replace `:443` with your domain name
3. Remove `auto_https off` and `tls internal`
4. Add your email in global options
5. Update frontend environment variables in docker-compose.yml

### To disable HTTPS (not recommended):
1. Remove the caddy service from docker-compose.yml
2. Add port mapping back to frontend service: `- "3000:3000"`
3. Update frontend environment variables to use HTTP URLs

## Security Considerations

- Self-signed certificates are suitable for development and internal use
- For production with public access, use a proper domain and Let's Encrypt certificates
- All HTTP traffic is automatically redirected to HTTPS
- Security headers are configured to prevent common attacks
- HSTS is enabled with shorter duration for self-signed certificates
