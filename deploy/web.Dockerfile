FROM node:22.19.0-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
COPY public ./public
RUN npm run build

FROM alpine:3.21
WORKDIR /app
COPY --from=build /app/dist ./dist
CMD ["sh", "-c", "cp -a /app/dist/. /static/ && exec sleep infinity"]
