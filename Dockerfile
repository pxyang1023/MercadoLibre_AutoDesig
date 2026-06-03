FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir pillow

ENV HOST=0.0.0.0
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "scripts/server_v1.py"]
