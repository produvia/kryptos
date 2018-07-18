#!/bin/bash

ids=$(docker ps -a -q)
for id in $ids
do
  echo "$id"
  docker stop $id && docker rm $id
done

bash docker_scripts/build-frontend.sh

docker build -t kryptos-prod:latest -f Dockerfile .
