# Kryptos

## About

Kryptos AI is a virtual investment assistant that manages your cryptocurrency portfolio. To learn more, check out the [Kryptos Slide Deck](https://docs.google.com/presentation/d/1O3BQ6fS9SuokJud8TZ1XPXX5QbjefAEiXNR3cxJIJwE/view) and the [Kryptos White Paper](https://docs.google.com/document/d/1Um9yoosEj-oZdEF3yMK2pt5TI0O2aRYhgkC0XJf_BVo/view).


## Installation

To get the entire project up and running locally:


Clone the repo:
```bash
$ git clone https://github.com/produvia/cryptocurrency-trading-platform.git
$ cd cryptocurrency-trading-platform
```

Build the docker images
```bash
docker-compose build
```


## Running locally

Run all the docker containers

```bash
$ bash docker_scripts/dev-start.sh
```

Browse to http://0.0.0.0:5000

## Deployment

### First push the base image to GCR

This speeds up the build process during deployment by caching from the heavy docker base image

Build the base image
docker build -t kryptos-base -f core/Dockerfile-base /core
docker build -t kryptos-worker -f core/Dockerfile-worker /core
docker buildt -t kryptos-app -f app/Dockerfile /app

tag for gcr
docker tag kryptos-base gcr.io/kryptos-stage/kryptos-base:latest
docker tag kryptos-worker gcr.io/kryptos-stage/kryptos-worker:latest
docker tag kryptos-app gcr.io/kryptos-stage/kryptos-app:latest

Push images
docker push gcr.io/kryptos-stage/kryptos-base:latest
docker push gcr.io/kryptos-stage/kryptos-worker:latest
docker push gcr.io/kryptos-stage/kryptos-app:latest

# Deploy
gcloud app deploy app/app.yaml --image-url=gcr.io/kryptos-stage/kryptos-app:latest
gcloud app deploy /core/worker.yaml --image-url=gcr.io/kryptos-stage/kryptos-worker:latest
gcloud app deploy --image-url=[HOSTNAME]/[PROJECT-ID]/[IMAGE]:[TAG]


## Project Components

To work with the core kryptos code base:

Checkout the [core documentation](core/README.md)
