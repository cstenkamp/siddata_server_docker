# Howto: Docker

*Note: In this text, I'll often talk about commands you can run. If you are unsure of their usage, you can always run `<cmd_name> --help` to get information about what exactly the command does and what arguments it accepts!*

## What is Docker?

**Docker** is a system which allows you isolate applications into so-called **containers**. Such a container can be compared to a **virtual machine**, except that it is a lot more efficient and doesn't need to additionally contain a complete operating system. These containers are isolated from one another and bundle their software together with all required dependencies, libraries and configuration files. This means, that if a software is bundled into a container, you don't need to install anything on the computer you run the container from (the "host OS"), but can simply download and run the container and be done with it. To create a Docker-Container, you need to write a `Dockerfile` which contains exact, reproducible instructions on what needs to be set up for the virtual operating system inside the container.

Generally, one Docker-Container should contain exactly one service or application. **Docker-Compose** is small convenience-system ontop of docker that allows to easily specify configurations for multiple containers that work together and communicate with each other, like the Postgres-Database and the actual Siddata Backend. A file named `docker-compose.yml` contains the configurations for the individual containers.

### How do I use Docker?

If you do not use docker-compose, you first have to create an `image` from the `Dockerfile` using the command `docker build`. Such an image contains all the required files and can be shared using eg. Dockerhub or the Github Container Registry. To start an image, you need the command `docker run`, which makes a `container` out of the image - you can thus see an `image` as a blueprint of a `container`, while the container is the instantiation of an image (much like classes and objects in OOP). That also means, that the same image can be the basis of multiple containers (which may differ for example depending on which directories from your host OS you mount into the container or what environment-variables you pass to it). If you use docker-compose, the command `docker-compose up` is enough to both build multiple images as required and start the corresponding containers. You can list all images on your system using `docker image ls [-a]` and all containers using `docker container ls [-a]` or `docker ps`.

Once a container is started, it executes whatever was specified as its `entrypoint` (specified in the `Dockerfile`) or `command` (specified in the `docker-compose.yml`). While a container should only execute one thing at a time (and does so really efficiently, in contrast to virtual machines!), you can execute arbitrary programs from running containers (which will invoke a new terminal-session and not interrupt other running processes). As almost all containers are based on some form of Linux, they generally ship with `bash` pre-installed into the containers, which means you can open a terminal inside any container, in which you can then navigate using `cd` and `ls` and execute other stuff from inside the container at will. To open another program from a running container, you can execute `docker exec [-i] [-t] <container_name> <command_to_run>`. Note that the `command_to_run` must either be in a directory that's part of the `PATH` of the container, or you must specify an absolute path to the command. In general however, running `docker exec -it <container_name> bash` should always work, and from there on you can navigate in the container at will. In general, `exec`ing a docker-container behaves pretty much like `sudo` or `ssh` does. Use CTRL+D to exit the session inside the container.

## What containers are used for this project?

Use `docker ps` to see which containers are active. In Dev-Settings there should be the following:

* `siddata_server_backend_1` with the actual Django-Backend (..and the `src`-directory is linked there so changes in code are directly reflected)
* `siddata_server_db_1` with the database, exposing port `5432` to other containers and your host-PC (which means it should be available on your host-PC in a web-browser under the domain *[http://localhost:5432](http://localhost:5432)*)
* `docker_pgres_adminer_1` with a web-admin-page for the database, available from your host-machine as [http://localhost:8080/](http://localhost:8080/)
* `siddata_tfserving_1`, the service that runs the productive tensorflow-models, exposing them at port `8500`/`8501`.

In production settings, there is additionally the container `siddata_server_proxy_1`, which executes `nginx`, the webserver handling incoming requests from other computers, allowing the backend to be exposed to the internet at large on the default-HTTP-Port [`80`](http://localhost:80). It can deal with many simultaneous users at once (in contrast to if you invoke Django using `mange.py runserver`!), and forwards the request internally to the `siddata_server_backend_1` container.

## What else do I need to know for this project?

* The database is in another container than the django-backend. Containers can communicate to each other by replacing `localhost` or the IP for socket-based communication with the name of the container, if it's specified correspondingly  in the `docker-compose.yml`
* To run a terminal *inside* the container `siddata_server_backend_1`, run `docker exec -it siddata_server_backend_1 bash`. The arguments `-it` mean *open in a new interactive terminal*, then the name of the container, then what you want to start. You can run anything (..that is in the container's PATH) using a command like this, for example also `docker exec -it siddata_server_db_1 ls` to see the contents of the base directory or `docker exec -it siddata_server_backend_1 python manage.py createsuperuser`.
* If you want to create or restore a backup of the Database, you of course have to run that command from the db-container `siddata_server_db_1`.
* Keep in mind that if you're using Pipe-operators (`>` and `<`), you don't need a terminal, which means you don't need the `-t` flag, but only the `-i` flag. The command to load a backup-file to the dockerized DB is thus `docker exec -i siddata_server_db_1 psql -U siddata < path/to/your/backup_file`
