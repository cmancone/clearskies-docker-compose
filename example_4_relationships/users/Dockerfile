FROM ubuntu:20.04

WORKDIR /tmp

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata
RUN apt-get install -y wget build-essential python3-dev python3-pip python3-gdbm libmariadb-dev python3-tk tk-dev python3-mysqldb wait-for-it
RUN pip3 install uwsgi mygrations clearskies
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN wget 'https://raw.githubusercontent.com/cmancone/mygrations/master/mygrate.py' && \
    chmod a+x mygrate.py && \
    mv mygrate.py /usr/local/bin/mygrate.py

COPY apps apps
COPY api.py ./
COPY start_uwsgi.sh ./
COPY .env ./
COPY mygrate.conf ./
COPY database database

EXPOSE 5000
CMD "/tmp/start_uwsgi.sh"
