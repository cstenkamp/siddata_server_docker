# siddata_server

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI/CD - Master](https://github.com/virtUOS/siddata_server/actions/workflows/test_docker_publish.yml/badge.svg?branch=master)](https://github.com/virtUOS/siddata_server/actions/workflows/test_docker_publish.yml)


The joint project for Individualization of Studies through Digital, Data-Driven Assistants (SIDDATA, www.siddata.de) aims to encourage students  to define their own study goals and to follow them consistently. The data-driven environment will be able to give hints, reminders and recommendations appropriate to the situation, as well as regarding local and remote courses and Open Educational Resources (OER).  This repository contains the code for the backend server which collects, refines and analyses data to generate personalized recommendation.


## Installing

We are using Docker & Docker-Compose! That means you don't have to install all components on your local system, but can instead simply install docker and docker-compose, and then set up the container inside docker.

### Installing Docker

##### Windows
* Install Docker Desktop for Windows (https://docs.docker.com/docker-for-windows/install). Installer is >500mb so
  quite big, and installation requires a restart (and afterwards it prompted me to install https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi ), but just follow the instructions of the installer.
* Install Git for Windows: Download the `.exe` from https://git-scm.com/download/win and run the installer. In the install wizard, make sure that git can be used from the command prompt, otherwise you'd have to switch between shells when coding and committing to git. Further use one of the two commit unix style options. Other than that, you'll probably go for the openSSL as well as Windows default console as terminal emulator options.

##### Linux
```
sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt-get install docker-ce docker-ce-cli containerd.io -y
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
sudo apt-get install git -y
```

### Set up this project

Once you have docker installed, you should be able to open a terminal in the `/docker`-directory of this project and simply run
```
docker-compose up
```

Alternatively, if you're using PyCharm, you can also let Pycharm handle the container: For that, click on the run-dropdown menu at the top right -> "Edit Configuration" -> "Add Configuration" -> "+" -> "Docker Compose" -> Add the `docker-compose.yml` as Compose-file

If you changed anything about the containers, make sure to delete them before re-running `docker-compose up` using
```
docker container rm siddata_server_backend_1 siddata_server_db_1 siddata_server_proxy_1
```
On Linux, you also may have to remove the intermediate database - for that, run
```
sudo rm -rf data/db
```
So the 1-command-version to restart:
```
docker container rm siddata_server_backend_1 siddata_server_db_1 siddata_server_proxy_1 && sudo rm -rf ./data/db && docker-compose --env-file ./settings_prod.env -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up --build
```

### Set up manually

If you don't want to run everything in docker, you can still set up everything manually. For that, make sure you have conda installed:

* TODO you also have to install postgres etc!

#### Windows

* TODO

#### Linux

Run this to install Miniconda:
```
cd ~ && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && chmod +x Miniconda3-latest-Linux-x86_64.sh && ./Miniconda3-latest-Linux-x86_64.sh -b -p $PWD/conda && eval "$($PWD/conda/bin/conda shell.bash hook)" && SHELLNAME=$(/bin/ps -p $$ | grep -oE '[^ ]+$' | tail -1) && conda init $SHELLNAME && rm Miniconda3-latest-Linux-x86_64.sh && cd -
```

#### Afterwards/both

Open a new terminal, change directory to the root of this project, and
```
conda create -n siddata_p3f python=3.9
conda activate siddata_p3f
pip install -r requirements.txt
```
then, to run the backend, you can either run
```
python path/to/manage.py runserver 0.0.0.0
```

or you can run the same script that the container runs, which automatically migrates etc before running the server:
```
cd src
../docker/scripts/entrypoint_dev.sh
```

## Contributing

If you want to contribute, you can still run everything inside the docker-container. However, we are using `pre-commit` with linting hooks, such as `black` and `flake8`. To set these up for your local development environment, you need to install at least the `requirements-dev.txt` outside of any container. For that, you should run

```
#If you haven't set up your environment before:
conda create -n siddata_p3f python=3.9
```
```
conda activate siddata_p3f
pip install -r requirements-dev.txt
pre-commit install
```
Note that if your code needs to be reformatted, these pre-commit-hooks may change your files on commit. If there
were any changes by these hooks, the actual commit will be blocked, such that you may have to commit the files a
second time.


## Running productively

To run productively, you don't need anything installed on the machine you're using except docker and docker-compose. Create an environment-file `settings_prod.env` with the following keys:
```
ALLOWED_HOSTS=...
```

and then simply run, from the base of this repo
```
docker-compose --env-file ./settings_prod.env -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up --build
```

TODO update Readme: Linux-users should use `docker_run_linux.sh`




############# updates

DOCKER-VERSION
* Windows: just setup the settings_prod.env (for local prod-testing "ALLOWED_HOSTS=localhost" should even be enough), and then run the `docker-compose --env-file ./settings_prod.env -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up --build` command from the docker-directory, done.
* Linux: should use `docker_run_linux.sh`

NON-DOCKER (harder! Not recommended!!)
Windows:
```
conda create -n siddata_p3f python=3.9
conda activate siddata_p3f
pip install -r requirements-dev.txt
pre-commit install
pip install -r requirements.txt
.\docker\scripts\entrypoint_dev.cmd (or manually migrating and then running manage.py runserver using pycharm)
```
