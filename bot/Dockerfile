FROM python:3.10-slim

WORKDIR /usr/src/app

EXPOSE 80

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "./src/main.py"]