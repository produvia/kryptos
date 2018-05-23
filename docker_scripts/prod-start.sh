#!/bin/bash

docker-compose -f docker-compose.yaml up -d
docker run \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$PWD:/rootfs/$PWD" \
    -w="/rootfs/$PWD" \
    docker/compose:1.13.0 \
    exec worker sh -c "catalyst ingest-exchange -x bitfinex &&
    catalyst ingest-exchange -x bittrex poloniex &&
    catalyst ingest-exchange -x bitfinex &&
    /bin/bash"
