# ==============================================================================
# Skills API - Frontend Dockerfile
# ==============================================================================
# Multi-stage build for Next.js frontend
# ==============================================================================

# ==============================================================================
# Dependencies Stage
# ==============================================================================
FROM node:20-alpine AS deps

WORKDIR /app

# Install dependencies based on the preferred package manager
COPY web/package.json web/package-lock.json* ./

RUN npm ci

# ==============================================================================
# Builder Stage
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY web/ .

# Build arguments for environment URLs (used at build time)
ARG NEXT_PUBLIC_API_URL=http://localhost:62610
ARG NEXT_PUBLIC_DOCS_URL=http://localhost:62630

# Set environment variables for build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_DOCS_URL=$NEXT_PUBLIC_DOCS_URL

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# ==============================================================================
# Production Stage
# ==============================================================================
FROM node:20-alpine AS production

WORKDIR /app

# Set environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Install sharp for image optimization in standalone mode
RUN npm install sharp

# Set correct permissions for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Copy public directory
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Copy entrypoint script
COPY --chown=nextjs:nodejs docker/web/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 62600

# Set hostname
ENV HOSTNAME="0.0.0.0"
ENV PORT=62600

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget -q --spider http://localhost:62600/ || exit 1

# Start the server with warmup
ENTRYPOINT ["/entrypoint.sh"]
