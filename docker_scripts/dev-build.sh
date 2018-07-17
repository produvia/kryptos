#!/bin/bash
ids=$(docker ps -a -q)
for id in $ids
do
  echo "$id"
  docker stop $id && docker rm $id
done

echo "Rebuilding frontend"
rm -rf kryptos/app/static/spa-mat
cd frontend/ quasar clean && quasar build && cd ..
cp -r frontend/dist/spa-mat kryptos/app/static/spa-mat

docker build -t krpytos-dev -f Dockerfile .
