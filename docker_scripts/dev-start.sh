#!/bin/bash

# runs quasar dev server and starts docker container to allow live reloads
cd frontend && node node_modules/quasar-cli/bin/quasar-dev &
docker-compose -f docker-compose.dev.yaml up -d
docker-compose exec worker /bin/bash
