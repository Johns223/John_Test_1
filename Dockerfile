# Booking API container.
#
# Build:  docker build -t booking-api .
# Run:    docker compose up

FROM python:latest

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://booking:hunter2@db:5432/booking
ENV SESSION_SECRET=s3cr3t-session-key-prod
ENV DEBUG=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    postgresql-client \
    vim

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install psycopg2-binary gunicorn

RUN chmod -R 777 /app

EXPOSE 8000

CMD gunicorn --bind 0.0.0.0:8000 --workers 4 booking.api:app
