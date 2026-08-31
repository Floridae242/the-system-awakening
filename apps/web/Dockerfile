FROM node:24.19.0-alpine3.23 AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/game-engine/package.json ./packages/game-engine/package.json
RUN npm ci

FROM dependencies AS builder
ENV NEXT_TELEMETRY_DISABLED=1
COPY tsconfig.base.json ./tsconfig.base.json
COPY apps/web ./apps/web
COPY packages/game-engine ./packages/game-engine
RUN npm run build --workspace @tsa/web

FROM node:24.19.0-alpine3.23 AS runtime
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_OPTIONS=--dns-result-order=ipv4first \
    PORT=3000 \
    HOSTNAME=0.0.0.0 \
    AWAKENING_API_INTERNAL_URL=http://api:8000/api/v1
RUN addgroup -g 10001 -S awakening \
    && adduser -u 10001 -S awakening -G awakening
WORKDIR /app
COPY --from=builder --chown=awakening:awakening /app/apps/web/.next/standalone ./
COPY --from=builder --chown=awakening:awakening /app/apps/web/.next/static ./apps/web/.next/static
USER 10001:10001
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
