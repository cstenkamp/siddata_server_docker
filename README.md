# siddata_server
The joint project for Individualization of Studies through Digital, Data-Driven Assistants (SIDDATA, www.siddata.de) aims to encourage students  to define their own study goals and to follow them consistently. The data-driven environment will be able to give hints, reminders and recommendations appropriate to the situation, as well as regarding local and remote courses and Open Educational Resources (OER).  This repository contains the code for the backend server which collects, refines and analyses data to generate personalized recommendation.


## Contributing

We are using Docker & Docker-Compose!

Pycharm:
* "Add Configuration" -> "+" -> "Docker Compose" -> Add the `docker-compose.yml` as Compose-file
* After checking out the repo, do this:
```
cd path/to/repositoryroot
cp siddata_server/settings_default.py siddata_server/settings.py
docker-compose run web python manage.py makemigrations
sudo chown -R $(id -u):$(id -g) data #only necessary on Linux
#and then to start:
sudo docker-compose up
```