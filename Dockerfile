FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app

CMD ["/bin/sh", "/app/startup.sh"]