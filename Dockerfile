# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY backend ./backend

ENV FLASK_APP=backend.app
EXPOSE 8000

CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
