FROM tiangolo/uwsgi-nginx-flask:python3.6

# copy only the requirements to prevent rebuild for any changes
COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt


# Above lines represent the dependencies
# below lines represent the actual app
# Only the actual app should be rebuilt upon changes
COPY . /app

# Install kryptos package
WORKDIR /app


# NGINX config
ENV UWSGI_INI /app/uwsgi.ini


ENV REDIS_HOST REDIS

EXPOSE 80
