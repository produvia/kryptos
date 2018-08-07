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
docker-compose up -d
```

This will spin up a web, worker, postgres, and redis container.

The web app will be accessible at http://0.0.0.0:8080



## Connecting to the CloudSQL database locally

To connect to the production database instead of the docker container, install the google cloud local cloud-sql-proxy
```bash
./cloud_sql_proxy -instances=kryptos-205115:us-west1:kryptos-db=tcp:5432
```


## Deployment

### Initial deployement setup
If this is the first time deploying, begin by pushing the images to GCR

```bash
# first build and push the base and worker images
cd /core
gcloud builds submit --tag gcr.io/kryptos-205115/kryptos-base -f Dockerfile-base --timeout 1200 .
gcloud builds submit --tag gcr.io/kryptos-205115/kryptos-worker --timeout 1200 .

# then the app image
cd /app
gcloud builds submit --tag gcr.io/kryptos-205115/kryptos-app . --timeout 1200
```

```bash
# we could drop the image_url, but this way is quicker
gcloud app deploy app.yaml --image-url=gcr.io/kryptos-205115/kryptos-app
```

### Set up the worker Compute Instance Template

In the Google Cloud console, create a new Instance Template

- select `Deploy a container image to this VM instance`
- Allocate a buffer for STDIN and psuedo-TTY
- Add the following command arguments (to enable logs)
    - `--log-driver=gcplogs`
    - `--log-opt gcp-log-cmd=true`
- Set the `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD` env variables
-Create a host directory mount
    - Mount path: `/root/.catalyst`
    - Host path: `catalyst-dir`
    - Read/Write

Once the template is setup you can create new VMs from it which will pull and start the latest worker image



### Triggered deployments
There are three build triggers in place to help automate the deployments

1. The first rebuilds the base Dockerfile if a commit is pushed that changes Dockerfile-base
2. The second rebuilds the worker image if a pushed commit changes any files in the /core directory
3. The third rebuilds and deploys the app/default service if changes are made to the /app directory

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
