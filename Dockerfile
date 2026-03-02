FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /app/logs

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	LOG_LEVEL=INFO \
	LOG_FILE=/app/logs/app.log \
	LOG_MAX_BYTES=10485760 \
	LOG_BACKUP_COUNT=5

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

EXPOSE 8000

CMD ["python", "src/main.py"]