# Install Instructions

This file will guide you how to install this project in the following ways:

1. Using Docker
    * Using Docker & Windows
    * Using Docker & Linux
2. Manually
    * Using Windows
    * Using Linux
3. Using Docker for productive settings on Linux

**Note that if you're developing for this project, you still have to follow the instructions at [doc/readme_developer.md](https://github.com/virtUOS/siddata_server/blob/develop/doc/readme_developer.md)!!**

## Set up using Docker

To learn more about docker, have a look at [doc/howto_docker.md](https://github.com/virtUOS/siddata_server/blob/develop/doc/howto_docker.md)!

### Installing Docker

If you have installed Docker already (for example because you have installed the Frontend already), you can skip this step.

#### Installing Docker on Windows
* Install Docker Desktop for Windows (https://docs.docker.com/docker-for-windows/install). Installer is >500MB and installation requires a restart (and afterwards prompts to install https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi) - but just follow the instructions of the installer.
* Install Git for Windows: Download the `.exe` from https://git-scm.com/download/win and run the installer. In the install wizard, make sure that git can be used from the command prompt, otherwise you'd have to switch between shells when coding and committing to git. Further use one of the two commit unix style options. Other than that, you'll probably go for the openSSL as well as Windows default console as terminal emulator options.

#### Installing Docker on Linux
Run the following commands in a terminal:
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

### Set up the actual project

**Note that depending on your OS you have to read the sub-section Windows/Linux, as well as the "All OS" sub-section!**

#### Windows

Once you have docker installed, you should be able to open a terminal in the `/docker`-directory of this project and simply run
```
docker-compose up
```

Alternatively, if you're using PyCharm, you can also let Pycharm handle the container: For that, click on the run-dropdown menu at the top right -> "Edit Configuration" -> "Add Configuration" -> "+" -> "Docker Compose" -> Add the `docker-compose.yml` as Compose-file

#### Linux

On Linux, directories created inside containers are not owned by the host user, which is why all directories used in the containers need to be created before running the containers. For that, a shell-file is given that does so and needs to be run:

```
cd docker
./docker_run_linux.sh
```

If anything goes wrong, you may have to remove the intermediate database by running `sudo rm -rf django_data/db`.

#### All OS

If you changed anything about the containers, make sure to delete them before re-running them, using `docker container rm siddata_server_backend_1 siddata_server_db_1 siddata_server_proxy_1`.

Note again, that if you're developing for this project, even if you installed everything into a docker-container, you still have to follow certain requirements on your Host OS! Please consult [doc/readme_developer.md](https://github.com/virtUOS/siddata_server/blob/develop/doc/readme_developer.md) for that!


## Set up without using Docker

If you don't want to run everything in Docker, you can still set up everything manually. For that, you have to install `conda` and `postgresql`.  Note that this installation-process is harder, takes longer and is more error-prone, so it is only recommended if you know what you're doing!

### Installing conda and postgresql

#### Windows

* Install Postgresql: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads ([more here](https://git.siddata.de/siddata/documentation/src/branch/master/DOKU_SIDDATA_entwicklungsumgebung_einrichtung%28wip%29_v1_windows.md#postgresql-installieren-und-datenbank-anlegen))
* Install Miniconda: https://docs.conda.io/en/latest/miniconda.html

#### Linux

Run this to install Miniconda:
```
cd ~ && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && chmod +x Miniconda3-latest-Linux-x86_64.sh && ./Miniconda3-latest-Linux-x86_64.sh -b -p $PWD/conda && eval "$($PWD/conda/bin/conda shell.bash hook)" && SHELLNAME=$(/bin/ps -p $$ | grep -oE '[^ ]+$' | tail -1) && conda init $SHELLNAME && rm Miniconda3-latest-Linux-x86_64.sh && cd -
```

Run this to install Postgresql:
```
sudo apt-get install postgresql
```

### Set up the actual project

#### All OS

Open a new terminal, change directory to the root of this project, and
```
conda create -n siddata_p3f python=3.9
conda activate siddata_p3f
pip install -r requirements.txt
```

This will set up the basic requirements. **Note that if you're developing for this project, you still have to follow the instructions at [doc/readme_developer.md](https://github.com/virtUOS/siddata_server/blob/develop/doc/readme_developer.md)!!**

### Run the project

#### Using Windows (Terminal)

To run the backend, you can either run the same script that the container runs, which automatically migrates etc before running the server:

```
.\docker\scripts\entrypoint_dev.cmd
```

Or you can run `manage.py` manually:

```
set PYTHONPATH=.\src
python src\manage.py runserver 0.0.0.0
```

Note that for the latter variant, you have to manually perform migrations and the like, so it is **not recommended**!

#### Using Linux (Terminal)

To run the backend, you can either run the same script that the container runs, which automatically migrates etc before running the server:

```
cd src
../docker/scripts/entrypoint_dev.sh
```

Or you can run `manage.py` manually:

```
PYTHONPATH=./src python src/manage.py runserver 0.0.0.0
```

Note that for the latter variant, you have to manually perform migrations and the like, so it is **not recommended**!

#### Using Pycharm (both OS)

If you want to run this project from inside Pycharm, make sure to mark the `src` directory as sources root: click onto the `src`-directory -> "Mark Directory as" -> "Sources Root"



## Using Docker for productive settings on Linux

To run productively, you don't need anything installed on the machine you're using except `docker` and `docker-compose`. Create an environment-file `settings_prod.env` with the following keys:
```
ALLOWED_HOSTS=...
```
(for local prod-testing `ALLOWED_HOSTS=localhost` should even be enough)


and then simply run, from the base of this repo:
```
cd docker
./docker_run_linux.sh -p
```
