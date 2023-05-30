FROM python:3.10-slim

WORKDIR /usr/src/app

EXPOSE 80

COPY . .

RUN pip install -r requirements.txt

WORKDIR /usr/src/app/project

RUN python manage.py makemigrations
RUN python manage.py migrate

CMD ["gunicorn", "project.wsgi:application", "-c", "../gunicorn_config.py"]