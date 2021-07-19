#!/bin/bash

###### parse "-p" for prod #######
run_prod=false
OPTIND=1

while getopts 'p' opt; do
    case $opt in
        p) run_prod=true ;;
        *) echo 'Error in command line parsing' >&2
           exit 1
    esac
done
shift "$(( OPTIND - 1 ))"
###### / parse "-p" for prod #######


mkdir -p ../data/RM_professions;
mkdir -p ../django_data/db/data;

if "$run_prod"; then
    docker-compose --env-file ../settings_prod.env -f ./docker-compose.yml -f ./docker-compose.prod.yml up --build;
else
    docker-compose -f ./docker-compose.yml up --build;
fi
