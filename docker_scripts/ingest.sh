#!/bin/bash

docker exec -it worker sh -c "catalyst ingest-exchange -x bitfinex -f daily,minute &&
    catalyst ingest-exchange -x poloniex -f daily,minute &&
    catalyst ingest-exchange -x bitfinex -f daily,minute &&
    /bin/bash"
