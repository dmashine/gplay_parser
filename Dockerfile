# Сборка и запуск:
# docker build . -t gplay-parser
# docker run -p 8080:8080 -t gplay-parser
FROM ubuntu
COPY *.py /
COPY requirements.txt /
RUN apt-get update && apt-get -y upgrade && apt-get -y install \
    python3-dev \
    python3-pip \
    musl-dev \
    gcc \
    && pip3 install -r requirements.txt \
    && pip3 install virtualenv
RUN python3 -m virtualenv --python=python3 virtualenv
EXPOSE 80
CMD [ "python3", "server.py" ]
