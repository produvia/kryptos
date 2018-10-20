FROM python:3.6

# copy only the requirements to prevent rebuild for any changes
# need to have in subdir of app
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt


# Above lines represent the dependencies
# below lines represent the actual app
# Only the actual app should be rebuilt upon changes
COPY . /app

## all app code needs to be in /app/app
## uwsgi needs to be in /app

WORKDIR /app
ENTRYPOINT honcho start app updater
