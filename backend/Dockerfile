FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 8000

CMD python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn procure_to_pay.wsgi:application --bind 0.0.0.0:8000
