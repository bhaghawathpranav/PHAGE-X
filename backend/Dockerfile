FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PHAGEX_ENVIRONMENT=production

WORKDIR /app
RUN addgroup --system phagex && adduser --system --ingroup phagex phagex
COPY requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt
COPY app ./app
COPY data ./data
COPY artifacts ./artifacts
RUN mkdir -p /app/work && chown -R phagex:phagex /app/work
USER phagex
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
