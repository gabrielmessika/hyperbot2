FROM python:3.12.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock
COPY dist/hyperbot2-0.2.0-py3-none-any.whl /tmp/hyperbot2.whl
RUN mv /tmp/hyperbot2.whl /tmp/hyperbot2-0.2.0-py3-none-any.whl && pip install --no-cache-dir --no-deps /tmp/hyperbot2-0.2.0-py3-none-any.whl
WORKDIR /app
COPY config /app/config
USER 1000:1000
HEALTHCHECK --interval=10s --timeout=5s --start-period=25s --retries=3 CMD hyperbot2 health --data-root /data
ENTRYPOINT ["hyperbot2", "--config", "/app/config/outcomes.toml"]
CMD ["run", "--data-root", "/data", "--seconds", "900", "--blocked-seconds", "300", "--public-network"]
