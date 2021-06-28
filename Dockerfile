# syntax=docker/dockerfile:1
# see https://docs.docker.com/samples/django/
FROM python:3.9-slim-buster

ARG uid
ARG gid
ARG CODEDIR=/opt/siddata_backend

RUN apt-get update \
    && apt-get install -y bash git vim curl zsh htop tmux unzip\
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*


WORKDIR ${CODEDIR}
COPY . ${CODEDIR}
ENV PYTHONPATH=${WORKDIR}
ENV RUNNING_IN_DOCKER=1
ENV PYTHONUNBUFFERED=1

RUN ln -sf /usr/local/bin/python3 /usr/bin/python3
RUN ln -sf /usr/bin/python3 /usr/bin/python
RUN python3 -m pip install --upgrade pip
RUN ln -sf /usr/bin/pip3 /usr/bin/pip

RUN pip install -r requirements.txt

RUN groupadd -g ${gid} developer \
    && useradd -g developer -u ${uid} -m developer
RUN chown -R developer:developer ${CODEDIR}
USER developer
ENV HOME=/home/developer
