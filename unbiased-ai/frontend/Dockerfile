# Step 1: Build stage
FROM node:20-alpine AS build-stage

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (use ci for faster, more reliable builds)
RUN npm ci --silent

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Step 2: Production stage
FROM nginx:stable-alpine AS production-stage

# Install curl for healthchecks
RUN apk add --no-cache curl

# Copy build artifacts from build-stage
# Make sure Vite is building to 'dist' (default)
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Clean default nginx configs and copy our custom one
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Health check for ECS
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
