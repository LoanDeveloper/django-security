FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache build-base postgresql-dev
RUN adduser -D appuser

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown -R appuser:appuser /usr/src/app && chmod -R u+rwX /usr/src/app

USER appuser
EXPOSE 80
CMD ["python", "manage.py", "runserver", "0.0.0.0:80"]