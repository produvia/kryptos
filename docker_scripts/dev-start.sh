#!/bin/bash

# if [ ! "$(docker ps -q -f name=worker)" ]; then
#     if [ "$(docker ps -aq -f status=exited -f name=worker)" ]; then
#         # cleanup
#         docker rm worker
#     fi
#     # run your container
#     docker run -d --name worker -net=kryptos-net local-kryptos-rq
# else
#     docker run --name worker local-kryptos-rq
# fi


# if [ ! "$(docker ps -q -f name=web)" ]; then
#     if [ "$(docker ps -aq -f status=exited -f name=web)" ]; then
#         # cleanup
#         docker rm web
#     fi
#     # run your container
#     docker run -d -e FLASK_DEBUG=1 -e REDIS--name web -net=kryptos-net local-kryptos-main
# else
#     docker run -d -e FLASK_DEBUG=1 --name web -net=kryptos-net local-kryptos-main # debug!
# fi

# # docker exec -it web sh -c "catalyst ingest-exchange -x bitfinex && catalyst ingest-exchange -x bitfinex"

docker-compose -f docker-compose.dev.yaml up -d