# Multi-stage Dockerfile for FocusBoard React Frontend
# Stage 1: Build the React SPA
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve with lightweight high-performance Nginx
FROM nginx:alpine

# Remove default nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy production build from Stage 1
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with SPA HTML5 fallback
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
