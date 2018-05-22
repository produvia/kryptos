#!/bin/bash

# if [ ! "$(docker ps -q -f name=worker)" ]; then
#     if [ "$(docker ps -aq -f status=exited -f name=worker)" ]; then
#         # cleanup
#         docker rm worker
#     fi
#     # run your container
#     docker run -d --name gcr.io/kryptos-204204/krpytos-rq
# else
#     docker run -d --name gcr.io/kryptos-204204/krpytos-rq
# fi


# if [ ! "$(docker ps -q -f name=web)" ]; then
#     if [ "$(docker ps -aq -f status=exited -f name=web)" ]; then
#         # cleanup
#         docker rm web
#     fi
#     # run your container
#     docker run -d --name web gcr.io/kryptos-204204/krpytos-main
# else
#     docker run -d --name worker gcr.io/kryptos-204204/krpytos-main
# fi

# docker exec -it web sh -c "catalyst ingest-exchange -x bitfinex && catalyst ingest-exchange -x bitfinex"
# docker exec -it web /bin/bash

docker-compose -f docker-compose.yaml up -d