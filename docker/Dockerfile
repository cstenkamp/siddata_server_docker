# syntax=docker/dockerfile:1
# see https://docs.docker.com/samples/django/
FROM python:3.9-slim-buster

ARG uid
ARG gid
ARG CODEDIR=/opt/siddata_backend/

#setup basic stuff

RUN echo $ALLOWED_HOSTS

RUN apt-get update \
    && apt-get install -y bash git vim curl zsh htop tmux unzip gcc libc-dev dos2unix \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/local/bin/python3 /usr/bin/python3
RUN ln -sf /usr/bin/python3 /usr/bin/python
RUN python3 -m pip install --upgrade pip
RUN ln -sf /usr/bin/pip3 /usr/bin/pip

#copy and install our code and set env-vars

WORKDIR ${CODEDIR}
#COPY src ${CODEDIR}
COPY docker/scripts /scripts
RUN chmod +x /scripts/*
RUN dos2unix /scripts/entrypoint_dev.sh /scripts/entrypoint_prod.sh

ENV PYTHONPATH=${CODEDIR}
ENV RUNNING_IN_DOCKER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/scripts:${PATH}"

COPY ./requirements* ${CODEDIR}
COPY ./docker/requirements* ${CODEDIR}
RUN pip install -r requirements.txt
RUN pip install -r requirements-docker.txt

# nginx-stuff

# folder to serve media files by nginx
RUN mkdir -p /vol/web/media
# folder to serve static files by nginx
RUN mkdir -p /vol/web/static

#setup a non-root-user with same gid as our user and ensure it can access all the stuff

RUN groupadd -g ${gid} developer \
    && useradd -g developer -u ${uid} -m developer

RUN chown -R developer:developer ${CODEDIR}
RUN chown -R developer:developer /vol
RUN chmod -R 755 /vol/web
RUN chown -R developer:developer ${CODEDIR}
RUN chmod -R 755 ${CODEDIR}
RUN mkdir /opt/data
RUN chown -R developer:developer /opt/data
RUN mkdir /opt/django_data
RUN chown -R developer:developer /opt/django_data

USER developer
ENV HOME=/home/developer
