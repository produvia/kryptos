#!/bin/bash

docker tag kryptos-deps gcr.io/kryptos-204204/krpytos-deps:latest
docker tag kryptos-main gcr.io/kryptos-204204/krpytos-main:latest

docker push gcr.io/kryptos-204204/krpytos-deps:latest
docker push gcr.io/kryptos-204204/krpytos-main:latest
