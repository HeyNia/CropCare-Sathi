FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/static/uploads

EXPOSE 8080

CMD ["sh", "-c", "python -c \"from app import init_db; init_db()\" && waitress-serve --host=0.0.0.0 --port=8080 app:app"]