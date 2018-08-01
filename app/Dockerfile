FROM python:3.6

#TODO remove the need for ta-lib
# install TA_LIB library and other dependencies
RUN apt-get -y update \
    && apt-get -y install libfreetype6-dev libpng-dev libopenblas-dev liblapack-dev gfortran \
    && curl -L -O http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -zxf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && rm -rf ta-lib*

# copy only the requirements to prevent rebuild for any changes
# need to have in subdir of app
COPY requirements.txt /app/requirements.txt
RUN pip install numpy
RUN pip install ta-lib
RUN pip install -r /app/requirements.txt


# Above lines represent the dependencies
# below lines represent the actual app
# Only the actual app should be rebuilt upon changes
COPY . /app

## all app code needs to be in /app/app
## uwsgi needs to be in /app

WORKDIR /app

ENTRYPOINT gunicorn -b :8080 autoapp:app --log-level debug --timeout 90
