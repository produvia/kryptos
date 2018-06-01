FROM tiangolo/uwsgi-nginx-flask:python3.6
# If you're going to need to troubleshoot with vim
# RUN apt-get -y update && apt-get -y install vim


# install TA_LIB and other dependencies
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
COPY requirements.txt /app/requirements.txt

# ensure numpy installed before ta-lib, matplotlib, etc
RUN pip install 'numpy==1.14.3'
RUN pip install -r /app/requirements.txt


# Above lines represent the dependencies
# below lines represent the actual app
# Only the actual app should be rebuilt upon changes

COPY . /app

WORKDIR /app
RUN pip install -e .


ENV UWSGI_INI /app/kryptos/uwsgi.ini

ENV STATIC_URL /static
ENV STATIC_PATH /app/kryptos/app/static
ENV STATIC_INDEX 1
ENV REDIS_HOST REDIS


# VOLUME ['~/.catalyst']
# COPY ./nginx.conf /etc/nginx/conf.d/

EXPOSE 80