FROM python:3.10-alpine

WORKDIR /app

COPY . /app
RUN pip install -r requirements.txt


CMD ["/bin/sh", "/app/startup.sh"]