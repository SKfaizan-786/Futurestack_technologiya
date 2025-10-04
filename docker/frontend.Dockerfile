# MedMatch AI Frontend - Multi-stage React build for Docker MCP Gateway showcase
# Optimized for healthcare UI with static asset serving via nginx

# ================================
# Stage 1: Node.js build environment
# ================================
FROM node:18-alpine as node-builder

# Metadata for hackathon creativity
LABEL maintainer="MedMatch AI Team"
LABEL version="1.0.0"
LABEL description="React frontend for clinical trial matching platform"
LABEL hackathon.award="docker-mcp-gateway"
LABEL ui.framework="react-typescript"
LABEL optimization="multi-stage-creative"

# Set working directory
WORKDIR /app

# Install dependencies for better Docker layer caching
COPY frontend/package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/index.html ./
COPY frontend/vite.config.ts ./
COPY frontend/tsconfig*.json ./
COPY frontend/tailwind.config.js ./
COPY frontend/postcss.config.js ./

# Build the React application with optimizations
ENV NODE_ENV=production
RUN npm run build

# ================================
# Stage 2: Nginx static file server (Creative Docker MCP Gateway usage)
# ================================
FROM nginx:alpine as production

# Install additional tools for Docker MCP Gateway monitoring
RUN apk add --no-cache \
    curl \
    jq \
    bash

# Create custom nginx configuration for healthcare SPA
COPY --from=node-builder /app/dist /usr/share/nginx/html

# Custom nginx config for React Router and healthcare security headers
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers for healthcare applications
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.cerebras.ai https://*.supabase.co http://localhost:8000;" always;

    # Gzip compression for performance
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/json
        application/xml+rss;

    # Handle React Router (SPA routing)
    location / {
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Health check endpoint for Docker MCP Gateway
    location /health {
        access_log off;
        add_header Content-Type text/plain;
        return 200 "healthy\n";
    }

    # Metrics endpoint for monitoring
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }

    # API proxy to backend (for Docker MCP Gateway service mesh)
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for healthcare API calls
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Error pages
    error_page 404 /index.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
EOF

# Create health check script for Docker MCP Gateway integration
RUN cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
# Comprehensive health check for Docker MCP Gateway monitoring

# Check nginx is responding
if ! curl -f http://localhost/health > /dev/null 2>&1; then
    echo "FAIL: Nginx health check failed"
    exit 1
fi

# Check if React app is properly loaded
if ! curl -s http://localhost/ | grep -q "MedMatch"; then
    echo "FAIL: React app not loaded properly"
    exit 1
fi

# Check nginx status
if ! curl -s http://localhost/nginx_status > /dev/null 2>&1; then
    echo "WARN: Nginx status endpoint not accessible"
fi

echo "SUCCESS: Frontend health check passed"
exit 0
EOF

RUN chmod +x /usr/local/bin/health-check.sh

# Health check for Docker orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["/usr/local/bin/health-check.sh"]

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# ================================
# Stage 3: Development variant with hot reload
# ================================
FROM node:18-alpine as development

LABEL environment="development"
LABEL features="hot-reload,debugging"

WORKDIR /app

# Install all dependencies including dev dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy source code
COPY frontend/ .

# Expose Vite dev server port
EXPOSE 3000

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start development server with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ================================
# Creative Docker MCP Gateway Build Instructions:
# 
# Production Build:
# docker build --target production -t medmatch-frontend:prod -f docker/frontend.Dockerfile .
# 
# Development Build:
# docker build --target development -t medmatch-frontend:dev -f docker/frontend.Dockerfile .
# 
# Docker MCP Gateway Features Showcased:
# 1. Multi-stage builds for optimization
# 2. Security headers for healthcare compliance
# 3. Built-in health checks and monitoring endpoints
# 4. Nginx proxy for microservices architecture
# 5. Environment-specific variants (prod/dev)
# 6. Static asset optimization with caching
# 7. SPA routing support for React
# ================================