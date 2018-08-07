#!/bin/bash

docker-compose -f docker-compose.dev.yaml up -d

docker-compose exec web flask db upgrade
docker-compose logs -f web worker
# docker exec -it db /bin/bash
