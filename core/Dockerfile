FROM gcr.io/kryptos-stage/kryptos-base:latest

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

WORKDIR /core
ENTRYPOINT honcho start -f procfile worker monitor ingester
