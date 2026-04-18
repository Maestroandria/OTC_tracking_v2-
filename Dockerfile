FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/instance && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8080

CMD ["gunicorn", "-w", "2", "-b", ":8080", "wsgi:app"]
