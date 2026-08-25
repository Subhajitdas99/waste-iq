FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite bakes VITE_* variables into the JS bundle and the CSP at build time.
# Defaults preserve the existing local dev behavior; production overrides
# these via Compose build args or --build-arg.
ARG VITE_API_URL=http://localhost:8000
ARG VITE_APP_NAME=Waste-IQ
ARG VITE_SITE_URL=http://localhost:5173
ENV VITE_API_URL=$VITE_API_URL \
    VITE_APP_NAME=$VITE_APP_NAME \
    VITE_SITE_URL=$VITE_SITE_URL

RUN npm run build

FROM nginx:1.27-alpine

ENV PORT=80

COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
