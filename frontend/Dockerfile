# syntax=docker/dockerfile:1

# ---- build stage: Node compiles the React app into static files ----
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm test && npm run build

# ---- runtime stage: unprivileged Nginx serves dist/ (no Node in the final image) ----
FROM nginxinc/nginx-unprivileged:1.30-alpine
USER root
RUN apk upgrade --no-cache
USER 101

# Where Nginx proxies /api. Docker Compose uses the "backend" service name;
# Helm overrides this with the in-cluster backend Service.
ENV BACKEND_URL=http://backend:8000

# The image's entrypoint renders /etc/nginx/templates/*.template with envsubst
# into /etc/nginx/conf.d/ at startup.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
