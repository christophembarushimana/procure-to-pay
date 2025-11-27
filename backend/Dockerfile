FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN chmod +x render-start.sh

EXPOSE 8000

CMD ["./render-start.sh"]
