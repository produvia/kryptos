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
COPY requirements.txt /core/requirements.txt

# ensure numpy installed before ta-lib, matplotlib, etc
RUN pip install 'numpy==1.14.3'
RUN pip install -r /core/requirements.txt


# Above lines represent the dependencies
# below lines represent the actual app
# Only the actual app should be rebuilt upon changes
COPY . /core

# Install kryptos package
# COPY setup.py /core/setup.py
# COPY README.md /core/README.md

WORKDIR /core
RUN pip install -e .

WORKDIR /core/kryptos/worker
ENTRYPOINT honcho start -f /core/procfile worker monitor ingester
