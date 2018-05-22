#!/bin/bash

docker build -t gcr.io/kryptos-204204/krpytos-deps:latest -f Dockerfile-deps .
docker build -t gcr.io/kryptos-204204/krpytos-main:latest -f Dockerfile .