#!/bin/bash

docker-compose -f docker-compose.dev.yaml up -d
docker-compose exec worker /bin/bash
