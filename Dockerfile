FROM python:3.8-slim-buster

RUN apt-get -y update
RUN apt-get install -y --fix-missing \
    build-essential \
    cmake

WORKDIR /app
COPY . /app

RUN pip3 install -r requirements.txt

CMD ["uwsgi", "app.ini"]