# =============================================================================
# SkillForge AI — Frontend Dockerfile (Multi-stage)
#
# Stage 1 (builder): Node.js — installs dependencies, builds the React app
# Stage 2 (serve):   Nginx  — serves the built static files
#
# VITE_API_BASE_URL is passed as a build ARG so the browser knows where to
# reach the backend API. It is baked into the JS bundle at build time.
# The browser connects directly to localhost:8000 (the published Docker port).
# =============================================================================

# ---- Stage 1: Build ----
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests first for layer caching
COPY package.json package-lock.json ./

# Install dependencies (ci ensures exact lockfile reproduction)
RUN npm ci

# Accept the API URL as a build argument.
# Default: http://localhost:8000 (works for local Docker Compose)
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Copy the rest of the source code (respects .dockerignore)
COPY . .

# Build the production bundle (outputs to /app/dist)
RUN node node_modules/vite/bin/vite.js build

# ---- Stage 2: Serve ----
FROM nginx:1.27-alpine

# Copy the compiled frontend from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration (SPA routing + security headers)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Nginx runs in the foreground by default in the official image
CMD ["nginx", "-g", "daemon off;"]
