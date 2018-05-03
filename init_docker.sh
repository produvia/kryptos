#!/bin/bash
docker build -f Dockerfile-base -t kryptos-deps .
docker build -t krytpos .
docker-compose up -d