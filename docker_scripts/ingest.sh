#!/bin/bash

docker-compose exec worker sh -c "catalyst ingest-exchange -x bitfinex &&
    catalyst ingest-exchange -x poloniex &&
    catalyst ingest-exchange -x bitfinex &&
    /bin/bash"
