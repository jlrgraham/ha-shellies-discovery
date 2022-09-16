FROM python:3.10-slim

RUN pip install paho-mqtt certifi
RUN mkdir /app

COPY run.py /app/run.py
COPY python_scripts /app/python_scripts

WORKDIR /app

CMD ["python", "run.py"]
