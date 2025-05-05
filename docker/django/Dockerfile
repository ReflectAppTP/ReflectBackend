FROM python:3.9-slim

WORKDIR /app

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py collectstatic --noinput

COPY . .
ENV PYTHONPATH="/app:${PYTHONPATH}"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "reflect_backend_app.wsgi:application"]

