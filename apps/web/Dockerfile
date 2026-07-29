FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 opspilot

COPY --from=builder /app/public ./public
COPY --from=builder --chown=opspilot:nodejs /app/.next/standalone ./
COPY --from=builder --chown=opspilot:nodejs /app/.next/static ./.next/static

USER opspilot

EXPOSE 3000
ENV PORT=3000

CMD ["node", "server.js"]
