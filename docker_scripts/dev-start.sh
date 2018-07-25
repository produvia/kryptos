#!/bin/bash

docker-compose -f docker-compose.dev.yaml up -d

docker-compose exec web flask db upgrade
# docker logs -f web
# docker exec -it db /bin/bash
