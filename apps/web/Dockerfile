FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# The standalone server binds to $HOSTNAME (defaulting to the container's
# own interface, not loopback) — without this, a healthcheck against
# localhost from inside the container can't connect even though the app
# is up and reachable from the host via the published port.
ENV HOSTNAME=0.0.0.0

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

# node:alpine ships busybox wget, so no extra package install is needed.
# Use 127.0.0.1 explicitly: "localhost" in this image resolves to ::1 first,
# and the Next.js standalone server only binds the IPv4 wildcard, so an
# IPv6-first lookup here would report connection-refused forever.
HEALTHCHECK --interval=10s --timeout=5s --retries=10 --start-period=10s \
    CMD wget -q -O /dev/null http://127.0.0.1:3000/api/health || exit 1

CMD ["node", "server.js"]
