#!/bin/bash
docker build -f Dockerfile-deps -t kryptos-deps .
docker build -t krytpos .

# docker build -f Dockerfile-rq -t kryptos-rq-dash .

chmod u+x start_docker.sh

./start_docker.sh



