FROM python:3.6.2-slim

RUN apt-get update && apt-get install -y make gcc libssl-dev git

COPY requirements.txt /tmp/pip3-requirements.txt
RUN pip3 install -r /tmp/pip3-requirements.txt

CMD ["python", "/src/main.py"]
