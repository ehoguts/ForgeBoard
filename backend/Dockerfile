FROM python:3.12-alpine@sha256:c5ba3deef00c7758561a0f03c26f44f10589263d40e732b8748e0d1f38f6dd89
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt requirements-dev.txt constraints.txt ./
RUN apk upgrade --no-cache && apk add --no-cache libstdc++ \
    && pip install --no-cache-dir --only-binary=:all: -r requirements-dev.txt \
    && addgroup -S -g 10001 app && adduser -S -D -u 10001 -G app app
COPY --chown=app:app . .
RUN chown -R app:app /app
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
