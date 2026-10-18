# ============================================================================
# STAGE 1: Build the React + TypeScript + Tailwind + Motion Frontend
# ============================================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ============================================================================
# STAGE 2: Production Python 3.12 + FastAPI + ADK 2.0 + Enterprise Data Vault
# ============================================================================
FROM python:3.12-slim AS production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install system essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy Enterprise Data Vault (22 files + pre-embedded 10-table SQLite replica)
COPY enterprise_data_vault/ /app/enterprise_data_vault/

# Copy Backend application code
COPY backend/ /app/backend/

# Copy compiled Frontend SPA from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

WORKDIR /app/backend
EXPOSE 8080

# Run Uvicorn bound to Cloud Run's $PORT (8080) with keep-alive for ADK/Voice
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --timeout-keep-alive 120"]
