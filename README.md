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

```bash
docker-compose up
```

This will spin up a web, worker, ml, postgres, and redis container.

The web app will be accessible at http://0.0.0.0:8080

You can also view the RQ dashboard at http://0.0.0.0:8080/rq


## Local Development

 To run the entire platform and use the web app and telegram bot:

```bash
docker-compose up
```

 To only view the logs of a desired service:
```bash
docker-compose up -d
docker-compose logs -f <web|worker|ml>
```

 To simply run strategies from CLI:
```bash
docker-compose up -d
docker exec -it worker /bin/bash
```

This will provide a command prompt inside the worker container from which you can run the `strat` command



For example, to work on the ML service:
```bash
# start all containers w/o logging
docker-compose up -d

# enter the worker shell
docker exec -it worker /bin/bash
```

Then to stream ML logs in a seperate terminal
```bash
docker-compose logs -f ml
```












## Connecting to the CloudSQL database locally

To connect to the production database instead of the docker container, install the google cloud local cloud-sql-proxy
```bash
./cloud_sql_proxy -instances=kryptos-205115:us-west1:kryptos-db=tcp:5432
```


## Deployment

### Initial deployement setup
If this is the first time deploying, begin by pushing the images to GCR

```bash
# worker
cd /core
gcloud builds submit --tag gcr.io/kryptos-205115/kryptos-worker --timeout 1200 .

# then the app image
cd /app
gcloud builds submit --tag gcr.io/kryptos-205115/kryptos-app . --timeout 1200

# then the ml image
cd /ml
gcloud builds submit --tag gcr.io/kryptos-205115/kryptos-ml . --timeout 1200
```

Then deploy the app and ml services to Google App engine using the pushed images

```bash
# we could drop the image_url, but this way is quicker

# in app/
gcloud app deploy app.yaml --image-url=gcr.io/kryptos-205115/kryptos-app

# in /ml/
gcloud app deploy ml.yaml --image-url=gcr.io/kryptos-205115/kryptos-ml

# in /core
gcloud app deploy worker.yaml --image-url=gcr.io/kryptos-205115/kryptos-worker
```



### Triggered deployments
There are three build triggers in place to help automate the deployments

1. The first rebuilds and deploys the worker image if a pushed commit changes any files in the /core directory
2. The third rebuilds and deploys the ml service if changes are made to the /ml directory
2. The third rebuilds and deploys the app/default service if changes are made to the /app directory

You can view the cloudbuild.yaml file in the /core and /app directories to see the steps

These steps are
- pulls the latest relevant image (which is why manual building needs to be done initially)
- rebuilds the image by caching the latest version (this speeds up the builds)
- Tags the the newly built image, making it the latest version

In the case of changes to the app directory, the new image is also deployed from the cloud

Always check to see if there were any errors or if the build was not triggered.


## Project Components

To work with the core kryptos code base:

Checkout the [core documentation](core/README.md)
