FROM python:3.6

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

# copy only the requirements to prevent rebuild for any changes
COPY requirements.txt /requirements.txt

# ensure numpy installed before ta-lib, matplotlib, etc
RUN pip install 'numpy==1.14.3'
RUN pip install -r /requirements.txt


# Above lines represent the dependencies
# below lines represent the actual app
# Only the actual app should be rebuilt upon changes
COPY ./kryptos /kryptos

# Install kryptos package
COPY setup.py /setup.py
COPY README.md /README.md

RUN pip install -e .


# # NGINX config
# ENV UWSGI_INI /app/api/uwsgi.ini
#
#
# ENV REDIS_HOST REDIS
#
# EXPOSE 80
