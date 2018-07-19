FROM tiangolo/uwsgi-nginx-flask:python3.6

# install xgboost library
RUN git clone --recursive https://github.com/dmlc/xgboost \
    && cd xgboost; make -j4

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

# install node and quasar to build frontend
RUN curl --silent --location https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get install --yes nodejs
RUN npm install -g quasar-cli

# npm install only run if frontend dependencies change
COPY frontend/package.json /app/frontend/package.json
WORKDIR /app/frontend
RUN npm install


# copy only the requirements to prevent rebuild for any changes
COPY requirements.txt /app/requirements.txt

# ensure numpy installed before ta-lib, matplotlib, etc
RUN pip install 'numpy==1.14.3'
RUN pip install -r /app/requirements.txt


# Build static dir from frontend - not used for dev env
COPY frontend /app/frontend
RUN node node_modules/quasar-cli/bin/quasar-build



# Above lines represent the dependencies
# below lines represent the actual app
# Only the actual app should be rebuilt upon changes
COPY . /app

# MV does not work for dev, bc files moutned as a volume
# Instead the dev-start script runs the quasar dev server seperately
RUN mv -v /app/frontend/dist/spa-mat /app/kryptos/app/web/static

# Install kryptos package
WORKDIR /app
RUN pip install -e .


# NGINX config
ENV UWSGI_INI /app/kryptos/uwsgi.ini
COPY kryptos_nginx.conf /etc/nginx/conf.d/kryptos_nginx.conf

ENV REDIS_HOST REDIS

ENV STATIC_INDEX 1
ENV STATIC_PATH /app/kryptos/app/web/static/
EXPOSE 80
