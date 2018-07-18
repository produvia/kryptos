#!/bin/bash
ids=$(docker ps -a -q)
for id in $ids
do
  echo "$id"
  docker stop $id && docker rm $id
done


docker build -t krpytos-dev -f Dockerfile .
