#!/bin/bash
set -x

if [[ ! -z $(docker ps | grep 'psql_integration') ]]
then
  docker stop 'psql_integration'
fi



if [[ ! -z $(docker ps | grep 'psql_integration') ]]
then
  docker stop 'psql_integration'
fi

docker run --rm -dp 5432:5432 --name 'psql_integration' -e POSTGRES_HOST_AUTH_METHOD=trust quay.io/airshipit/postgres:14.8
sleep 15

docker run --rm --net host quay.io/airshipit/postgres:14.8 psql -h localhost -c "create user airflow with password 'password';" postgres postgres
docker run --rm --net host quay.io/airshipit/postgres:14.8 psql -h localhost -c "create database airflow;" postgres postgres

