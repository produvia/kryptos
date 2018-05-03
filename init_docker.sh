#!/bin/bash
docker build -f Dockerfile-base -t kryptos-deps .
docker build -t krytpos .
docker-compose up -d

export kryptos=sudo docker exec -i -t kryptos_web_1 /bin/bash

# echo "\n\n$ Run 'sudo docker exec -i -t kryptos_web_1 /bin/bash' to enter the docker shell!"