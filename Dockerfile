# --- frontend build ---
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# --- runtime: FastAPI serving the API and the built frontend ---
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/
RUN uv sync --locked --no-dev
COPY --from=web /web/dist web/dist
ENV HOST=0.0.0.0 PORT=8000 WORLDPOP_WEB_DIST=/app/web/dist
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "worldpop-api"]
