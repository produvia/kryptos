#!/bin/bash

docker build -t gcr.io/kryptos-204204/krpytos-deps -f Dockerfile-deps .
docker build -t gcr.io/kryptos-204204/krpytos-main -f Dockerfile .

docker tag gcr.io/kryptos-204204/krpytos-main kryptos-main
