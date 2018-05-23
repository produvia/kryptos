#!/bin/bash

docker exec -it worker sh -c "catalyst ingest-exchange -x bitfinex &&
    catalyst ingest-exchange -x poloniex &&
    catalyst ingest-exchange -x bitfinex &&
    /bin/bash"
