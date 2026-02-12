# ==============================================================================
# Skills Documentation - Docusaurus
# ==============================================================================
# Multi-stage build for optimized production image
# ==============================================================================

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY docs/package*.json ./

# Install dependencies
RUN npm install

# Copy docs source
COPY docs/ ./

# Build static site
RUN npm run build

# Stage 2: Production (serve with Node)
FROM node:20-alpine AS runner

WORKDIR /app

# Install serve for static file serving and curl for health check
RUN apk add --no-cache curl && npm install -g serve

# Copy built files
COPY --from=builder /app/build ./build

EXPOSE 62630

# Health check using curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:62630/ || exit 1

# Serve the static site
CMD ["serve", "-s", "build", "-l", "62630"]
