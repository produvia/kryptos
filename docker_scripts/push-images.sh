#!/bin/bash

chmod a+x docker_scripts/prod-build.sh
/bin/bash docker_scripts/prod-build.sh

docker tag kryptos-main gcr.io/kryptos-204204/krpytos-main:latest

docker push gcr.io/kryptos-204204/krpytos-deps:latest
docker push gcr.io/kryptos-204204/krpytos-main:latest
