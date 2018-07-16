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


# Above lines represent the dependencies
# below lines represent the actual app
# Only the actual app should be rebuilt upon changes

COPY . /app


WORKDIR /app
RUN pip install -e .


ENV UWSGI_INI /app/kryptos/uwsgi.ini
COPY kryptos_nginx.conf /etc/nginx/conf.d/kryptos_nginx.conf

ENV REDIS_HOST REDIS


# VOLUME ['~/.catalyst']
# COPY ./nginx.conf /etc/nginx/conf.d/

EXPOSE 80
