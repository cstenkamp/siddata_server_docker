# Siddata Server

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI/CD - Master](https://github.com/virtUOS/siddata_server/actions/workflows/test_docker_publish.yml/badge.svg?branch=master)](https://github.com/virtUOS/siddata_server/actions/workflows/test_docker_publish.yml)


The joint project for Individualization of Studies through Digital, Data-Driven Assistants (SIDDATA, www.siddata.de) aims to encourage students  to define their own study goals and to follow them consistently. The data-driven environment will be able to give hints, reminders and recommendations appropriate to the situation, as well as regarding local and remote courses and Open Educational Resources (OER).  This repository contains the code for the backend server which collects, refines and analyses data to generate personalized recommendation.


## Installing

There are two ways of installing this project: Either using Docker-Compose, or manually. The former means that you don't have to install all components on your local system, but can instead simply install `docker` and `docker-compose`, and then set up the container inside docker. If you are not already deep into the technology stack of this project, this is the recommended way. Note that if you want to contribute to this project, you should still install a few requirements for static-code-checking upon commits.

The second possibility is to install everything (including `conda` and `postgresql`) manually on your computer. This way takes longer and is more error-prone than the first way, but allows for more customization. Note that even if you follow this way, you still have to install `docker` and `docker-compose`, as both the [Frontend](https://TODO) as well as the Tensorflow-models (relying on [TFX](https://www.tensorflow.org/tfx)) require docker-compose.

Next to the distinction of installing using Docker or not, another distinction is if you want to install *productively* or *for development*. If you want to set this up on a productive server, the settings and the way this Django-Project is invoked differ. In this project, different `docker-compose.yml`-files allow for setting this project up correctly both for developers and for productive serving, such that setting up this project on a fresh VM can be done using only a single command.

**For the complete guide on how to install/set up this project, see `docs/install.md`**


## Contributing

If you want to contribute, you can still run everything inside the docker-container. However, we are using `pre-commit` with linting hooks, such as `black` and `flake8`.

**Please read the file `doc/readme_developer.md` for instructions on how to set these up**.
