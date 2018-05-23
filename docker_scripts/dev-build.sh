#!/bin/bash

docker build -t krpytos-deps -f Dockerfile-deps .
docker build -t krpytos-main -f Dockerfile .
