# siddata_server
The joint project for Individualization of Studies through Digital, Data-Driven Assistants (SIDDATA, www.siddata.de) aims to encourage students  to define their own study goals and to follow them consistently. The data-driven environment will be able to give hints, reminders and recommendations appropriate to the situation, as well as regarding local and remote courses and Open Educational Resources (OER).  This repository contains the code for the backend server which collects, refines and analyses data to generate personalized recommendation.


## Installing

We are using Docker & Docker-Compose!

Pycharm:
* "Add Configuration" -> "+" -> "Docker Compose" -> Add the `docker-compose.yml` as Compose-file
* After checking out the repo (`cd .. && sudo rm -r siddata_server && git clone git@github.com:virtUOS/siddata_server.git && cd siddata_server && git checkout ci_cd`), do this:
```
cd path/to/repositoryroot
cp siddata_server/local_settings_default.py siddata_server/local_settings.py
docker-compose build
docker-compose run web python manage.py makemigrations
sudo chown -R $(id -u):$(id -g) data #only necessary on Linux
#and then to start:
SIDDATA_ALLOWED_HOSTS='["0.0.0.0"]' docker-compose up
```

## Contributing

If you want to contribute, you can still run everything inside the docker-container. However, we are using `pre-commit`
with linting hooks, such as `black` and `flake8`. To set these up for your local development environment, you need
to install at least the `requirements-dev.txt` outside of any container. For that, you should run
```
#activate an environment of your choice, such as conda:
conda create -n siddata_p3f python=3.9
conda activate siddata_p3f
pip install -r requirements-dev.txt
pre-commit install
```
Note that if your code needs to be reformatted, these pre-commit-hooks may change your files on commit. If there
were any changes by these hooks, the actual commit will be blocked, such that you may have to commit the files a
second time.
