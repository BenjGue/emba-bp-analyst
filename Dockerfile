# ── Stage 1 : dépendances ──────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Copier uniquement les fichiers de dépendances pour profiter du cache Docker
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2 : image finale ─────────────────────────────────────────────────
FROM python:3.12-slim

# Utilisateur non-root (sécurité)
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copier les dépendances compilées
COPY --from=builder /install /usr/local

# Copier le code source
COPY app/ ./app/

# Certificat SSL Azure MySQL (téléchargé à l'avance dans le build context)
COPY DigiCertGlobalRootG2.crt.pem ./DigiCertGlobalRootG2.crt.pem

# Permissions
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
