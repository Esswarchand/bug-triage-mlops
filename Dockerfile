FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim as runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup /entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh

RUN mkdir -p ml_artifacts && chown -R appuser:appgroup ml_artifacts

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import requests; response = requests.get('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]