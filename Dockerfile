FROM tiangolo/uwsgi-nginx-flask:python3.6
# If you're going to need to troubleshoot with vim
# RUN apt-get -y update && apt-get -y install vim

RUN git clone --recursive https://github.com/dmlc/xgboost \
    && cd xgboost; make -j4

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
RUN pip install --pre xgboost

RUN apt-get -y install \
	build-essential \
	python-dev \
	python-setuptools \
    python-pip

#Install scikit-learn dependancies
RUN apt-get -y install \
	python-numpy \
	python-scipy \
	libatlas-dev \
    libatlas3-base

    #Install scikit-learn
RUN pip install -U scikit-learn

# install node to build frontend
RUN apt-get install --yes curl
RUN curl --silent --location https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get install --yes nodejs
RUN npm install -g quasar-cli

# npm install only run if frontend dependencies change
COPY frontend/package.json /tmp/package.json
RUN cd /tmp && npm install


# Above lines represent the dependencies
# below lines represent the actual app
# Only the actual app should be rebuilt upon changes

COPY . /app
RUN cp -r /tmp/node_modules /app/frontend/node_modules/
WORKDIR /app/frontend
RUN node node_modules/quasar-cli/bin/quasar-build

WORKDIR /app
RUN pip install -e .


RUN mkdir -p /app/kryptos/app/static/spa-mat && mv /app/frontend/dist/spa-mat /app/kryptos/app/static/spa-mat


ENV UWSGI_INI /app/kryptos/uwsgi.ini
COPY kryptos_nginx.conf /etc/nginx/conf.d/kryptos_nginx.conf

ENV REDIS_HOST REDIS

ENV STATIC_INDEX 1
ENV STATIC_PATH /app/kryptos/app/static/spa-mat
# VOLUME ['~/.catalyst']
# COPY ./nginx.conf /etc/nginx/conf.d/



EXPOSE 80
