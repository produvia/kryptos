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

### Getting production info
To view GAE instance logs
```bash
$ gcloud app logs read -s <default|worker|ml|>
```
To view worker statuses, run the following inside the *core/* dir
```bash
$ rq info -c kryptos.settings
```
or for the web dashboard
```bash
$ rq-dashboard -c kryptos.settings
```

To connect to the production database, install the google cloud local cloud-sql-proxy
```bash
./cloud_sql_proxy -instances=kryptos-205115:us-west1:kryptos-db=tcp:5432
```
